package com.matheussantos.solem.ui

import android.Manifest
import android.app.*
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.*
import android.provider.Settings
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.matheussantos.solem.MainActivity
import com.matheussantos.solem.data.WalkSessionStore
import com.matheussantos.solem.domain.*
import kotlinx.coroutines.flow.MutableStateFlow
import com.google.android.gms.common.ConnectionResult
import com.google.android.gms.common.GoogleApiAvailability
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority

/** User-started foreground session. Totals persist; coordinates never leave RAM. */
class WalkLocationService : Service() {
    companion object {
        const val START = "solem.gps.START"
        const val STOP = "solem.gps.STOP"
        const val OWNER = "owner"
        const val EXERCISE = "exercise"
        private const val CHANNEL = "solem_walk_tracking"
        private const val NOTIFICATION = 104
        val state = MutableStateFlow(WalkSession())
        private var running = false
        fun restore(context: Context, owner: String) {
            if(running) return
            val saved=WalkSessionStore(context).read(owner)
            state.value=saved?.recovered(SystemClock.elapsedRealtime(),boot(context)) ?: WalkSession(owner=owner)
        }
        fun boot(context:Context)=Settings.Global.getInt(context.contentResolver,Settings.Global.BOOT_COUNT,-1)
    }
    private lateinit var manager: LocationManager
    private lateinit var store: WalkSessionStore
    private var listener: LocationListener? = null
    private var fused: FusedLocationProviderClient? = null
    private var fusedCallback: LocationCallback? = null
    private var useFused = false
    private var subscription = 0
    private var lastAttempt = 0L
    private val accumulator=WalkDistanceAccumulator()
    private val handler=Handler(Looper.getMainLooper())
    private var stoppedExplicitly=false
    private var waitingSince=0L
    private val watchdog=object:Runnable {
        override fun run() {
            if(!state.value.active) return
            val now=SystemClock.elapsedRealtime()
            val enabled=gpsEnabled()
            val signal=gpsSignal(state.value.lastFixElapsed,waitingSince,now,enabled,state.value.receivedElapsed)
            val gap=!enabled || now-(state.value.lastFixElapsed.takeIf {it>0} ?: waitingSince)>30_000
            if(gap) accumulator.breakSegment()
            val current=state.value
            publish(current.copy(signal=signal,
                hasGap=current.hasGap || gap, durationMillis=current.duration(now)))
            if(shouldReconnectLocation(now,current.receivedElapsed,waitingSince,lastAttempt,enabled)) {
                publish(state.value.copy(recoveryAttempts=state.value.recoveryAttempts+1,hasGap=true))
                requestUpdates()
            }
            if(!state.value.active) return
            notifyProgress()
            handler.postDelayed(this,5000)
        }
    }
    override fun onBind(intent: Intent?): IBinder? = null
    override fun onCreate() {
        super.onCreate()
        manager=getSystemService(Context.LOCATION_SERVICE) as LocationManager
        store=WalkSessionStore(this)
        (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(
            NotificationChannel(CHANNEL,"Medição de caminhada e corrida",NotificationManager.IMPORTANCE_LOW))
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val saved=if(intent==null) store.active() else store.read(intent.getStringExtra(OWNER).orEmpty())
        val owner=intent?.getStringExtra(OWNER) ?: saved?.owner.orEmpty()
        if(intent?.action==STOP) {
            if(state.value.owner==owner || !running) {
                if(!running && saved!=null) state.value=saved.recovered(SystemClock.elapsedRealtime(),boot(this))
                stopTracking()
            }
            return if(running) START_STICKY else START_NOT_STICKY
        }
        if(intent!=null && intent.action!=START) return START_NOT_STICKY
        if(running) return START_STICKY // Duplicate start never resets a measurement.
        if(owner.isBlank() || (intent==null && saved==null)) {stopSelf();return START_NOT_STICKY}
        val now=SystemClock.elapsedRealtime()
        val recovered=saved?.takeIf {it.pending}?.recovered(now,boot(this))
        state.value=(recovered ?: WalkSession(owner=owner,
            exercise=intent?.getStringExtra(EXERCISE) ?: "Caminhada",
            startedAtMillis=System.currentTimeMillis(),startedElapsedMillis=now,bootCount=boot(this)))
            .copy(active=true,pending=true,error=null,signal=GpsSignal.SEARCHING,lastFixElapsed=0,
                receivedElapsed=0,accuracyMeters=null,recoveryAttempts=0)
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED)
            return fail("Ative a localização precisa para medir caminhada/corrida. A distância anterior foi preservada.")
        try {
            if(Build.VERSION.SDK_INT>=29) startForeground(NOTIFICATION,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
            else startForeground(NOTIFICATION,notification())
            running=true; waitingSince=now; accumulator.breakSegment()
            publish(state.value)
            useFused=GoogleApiAvailability.getInstance().isGooglePlayServicesAvailable(this)==ConnectionResult.SUCCESS
            if(useFused) fused=LocationServices.getFusedLocationProviderClient(this)
            requestUpdates()
            if(!state.value.active) return START_NOT_STICKY
            handler.post(watchdog)
        } catch (_:SecurityException) {return fail("Permissão retirada ou GPS bloqueado pelo Android. Distância preservada; retome pelo app.")}
        catch (_:Exception) {return fail("GPS interrompido. Distância preservada; tente retomar pelo app.")}
        return START_STICKY
    }
    private fun gpsEnabled()=runCatching {manager.isProviderEnabled(LocationManager.GPS_PROVIDER)}.getOrDefault(false)
    private fun cancelUpdates() {
        subscription++ // Ignore late callbacks/tasks from removed requests or a previous session.
        listener?.let {runCatching {manager.removeUpdates(it)}}
        listener=null
        fusedCallback?.let {callback -> runCatching {fused?.removeLocationUpdates(callback)}}
        fusedCallback=null
    }
    private fun requestUpdates() {
        cancelUpdates()
        lastAttempt=SystemClock.elapsedRealtime()
        val generation=subscription
        try {
            if(useFused) {
                val callback=object:LocationCallback() {
                    override fun onLocationResult(result:LocationResult) {
                        if(generation!=subscription || !state.value.active) return
                        result.locations.sortedBy {it.elapsedRealtimeNanos}.forEach {accept(it)}
                    }
                }
                fusedCallback=callback
                state.value=state.value.copy(locationSource="Localização combinada do Android")
                val request=LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY,2000L)
                    .setMinUpdateIntervalMillis(1000L).setMinUpdateDistanceMeters(0f)
                    .setMaxUpdateDelayMillis(0L).setMaxUpdateAgeMillis(0L)
                    .setWaitForAccurateLocation(false).build()
                fused!!.requestLocationUpdates(request,callback,Looper.getMainLooper()).addOnFailureListener {error ->
                    if(generation==subscription && state.value.active) {
                        if(error is SecurityException) fail("Permissão de localização retirada. Distância preservada.")
                        else {useFused=false;requestUpdates()}
                    }
                }
            } else {
                if(!manager.allProviders.contains(LocationManager.GPS_PROVIDER)) {
                    fail("GPS não disponível neste aparelho. Distância preservada.");return
                }
                val callback=object:LocationListener {
                    override fun onLocationChanged(point:Location) {if(generation==subscription) accept(point)}
                    override fun onProviderDisabled(provider:String) {
                        if(generation!=subscription) return
                        accumulator.breakSegment()
                        publish(state.value.copy(signal=GpsSignal.DISABLED,hasGap=true));notifyProgress()
                    }
                    override fun onProviderEnabled(provider:String) {
                        if(generation!=subscription) return
                        // Do not reset totals, duration or the last trusted fix.
                        publish(state.value.copy(signal=GpsSignal.SEARCHING));notifyProgress()
                    }
                    @Deprecated("Required on Android 8/9")
                    override fun onStatusChanged(provider:String?,status:Int,extras:Bundle?) {}
                }
                listener=callback
                state.value=state.value.copy(locationSource="GPS por satélite · modo alternativo")
                manager.requestLocationUpdates(LocationManager.GPS_PROVIDER,2000L,0f,callback,Looper.getMainLooper())
            }
        } catch (_:SecurityException) {
            fail("Permissão retirada ou localização bloqueada pelo Android. Distância preservada; retome pelo app.")
        } catch (_:Exception) {
            if(useFused) {useFused=false;requestUpdates()}
            else fail("GPS interrompido. Distância preservada; tente retomar pelo app.")
        }
    }
    private fun accept(point:Location) {
        if(!state.value.active) return
        val now=SystemClock.elapsedRealtime()
        val elapsed=point.elapsedRealtimeNanos/1_000_000
        // Cached, duplicate and out-of-order points must not conceal a silent provider.
        if(elapsed<=state.value.receivedElapsed || elapsed<=0 || now-elapsed !in 0..15_000) return
        val accuracy=point.accuracy.toDouble().takeIf {point.hasAccuracy() && it.isFinite() && it>=0}
        val current=state.value.copy(receivedElapsed=elapsed,accuracyMeters=accuracy)
        val result=accumulator.accept(GpsFix(point.latitude,point.longitude,accuracy ?: Double.POSITIVE_INFINITY,elapsed),now)
        if(result.usable) {
            publish(current.copy(meters=current.meters+result.added,lastFixElapsed=elapsed,
                signal=GpsSignal.GOOD,hasGap=current.hasGap || result.gap,durationMillis=current.duration(now)))
        } else {
            state.value=current.copy(signal=GpsSignal.WEAK)
        }
        notifyProgress()
    }
    private fun publish(value:WalkSession) {
        val saved=store.save(value)
        state.value=if(saved) value else value.copy(error="Não foi possível proteger o rascunho no aparelho. Libere espaço antes de continuar.")
    }
    private fun notifyProgress() {
        if(Build.VERSION.SDK_INT<33 || ContextCompat.checkSelfPermission(this,Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED)
            runCatching {(getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).notify(NOTIFICATION,notification())}
    }
    private fun notification():Notification {
        val open=PendingIntent.getActivity(this,0,Intent(this,MainActivity::class.java),PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val stop=PendingIntent.getService(this,1,Intent(this,WalkLocationService::class.java).setAction(STOP).putExtra(OWNER,state.value.owner),PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val label=when(state.value.signal) {
            GpsSignal.GOOD -> "GPS recebendo sinal"
            GpsSignal.WEAK -> "Posição imprecisa · aguardando precisão; distância preservada"
            GpsSignal.DISABLED -> "Localização desligada · distância preservada"
            GpsSignal.LOST -> "Sinal GPS perdido · distância preservada"
            else -> "Buscando sinal GPS"
        }
        val precision=state.value.accuracyMeters?.let {" · erro estimado %.0f m".format(it)}.orEmpty()
        val text=label+" · %.3f km".format(java.util.Locale.US,state.value.meters/1000)+precision
        return NotificationCompat.Builder(this,CHANNEL).setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentTitle("Solem · caminhada/corrida").setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text+". Abra o treino para ver o estado da medição."))
            .setContentIntent(open).addAction(android.R.drawable.ic_media_pause,"Parar GPS",stop)
            .setOnlyAlertOnce(true).setOngoing(true).build()
    }
    private fun fail(text:String):Int {
        val current=state.value
        publish(current.copy(active=false,pending=true,error=text,signal=GpsSignal.INTERRUPTED,
            durationMillis=current.duration(SystemClock.elapsedRealtime()),hasGap=true))
        release();stopForeground(STOP_FOREGROUND_REMOVE);stopSelf()
        return START_NOT_STICKY
    }
    private fun stopTracking() {
        stoppedExplicitly=true
        val current=state.value
        publish(current.copy(active=false,pending=false,signal=GpsSignal.STOPPED,error=null,
            durationMillis=current.duration(SystemClock.elapsedRealtime())))
        release();stopForeground(STOP_FOREGROUND_REMOVE);stopSelf()
    }
    private fun release() {
        handler.removeCallbacks(watchdog)
        cancelUpdates();accumulator.breakSegment();running=false
    }
    override fun onDestroy() {
        if(!stoppedExplicitly && state.value.active) {
            val current=state.value
            publish(current.copy(active=false,pending=true,signal=GpsSignal.INTERRUPTED,hasGap=true,
                durationMillis=current.duration(SystemClock.elapsedRealtime())))
        }
        release()
        super.onDestroy()
    }
}
