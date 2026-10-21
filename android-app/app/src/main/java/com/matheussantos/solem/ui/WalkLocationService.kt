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
    private val accumulator=WalkDistanceAccumulator()
    private val handler=Handler(Looper.getMainLooper())
    private var stoppedExplicitly=false
    private var waitingSince=0L
    private val watchdog=object:Runnable {
        override fun run() {
            if(!state.value.active) return
            val now=SystemClock.elapsedRealtime()
            val signal=gpsSignal(state.value.lastFixElapsed,waitingSince,now,gpsEnabled())
            val gap=signal==GpsSignal.LOST || signal==GpsSignal.DISABLED
            if(gap) accumulator.breakSegment()
            val current=state.value
            publish(current.copy(signal=if(signal==GpsSignal.GOOD && current.signal==GpsSignal.WEAK) GpsSignal.WEAK else signal,
                hasGap=current.hasGap || gap, durationMillis=current.duration(now)))
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
            .copy(active=true,pending=true,error=null,signal=GpsSignal.SEARCHING,lastFixElapsed=0)
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)!=PackageManager.PERMISSION_GRANTED)
            return fail("Ative a localização precisa para medir caminhada/corrida. A distância anterior foi preservada.")
        try {
            if(Build.VERSION.SDK_INT>=29) startForeground(NOTIFICATION,notification(),ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
            else startForeground(NOTIFICATION,notification())
            running=true; waitingSince=now; accumulator.breakSegment()
            publish(state.value)
            if(!manager.allProviders.contains(LocationManager.GPS_PROVIDER)) return fail("GPS não disponível neste aparelho.")
            val callback=object:LocationListener {
                override fun onLocationChanged(point:Location) {accept(point)}
                override fun onProviderDisabled(provider:String) {
                    accumulator.breakSegment()
                    publish(state.value.copy(signal=GpsSignal.DISABLED,hasGap=true))
                    notifyProgress()
                }
                override fun onProviderEnabled(provider:String) {
                    waitingSince=SystemClock.elapsedRealtime()
                    publish(state.value.copy(signal=GpsSignal.SEARCHING,lastFixElapsed=0))
                    notifyProgress()
                }
                @Deprecated("Required on Android 8/9")
                override fun onStatusChanged(provider:String?,status:Int,extras:Bundle?) {}
            }
            listener=callback
            // GPS only: do not interleave less precise network positions.
            // Zero minDistance lets us distinguish standing still from missing fixes.
            manager.requestLocationUpdates(LocationManager.GPS_PROVIDER,2000L,0f,callback,Looper.getMainLooper())
            handler.post(watchdog)
        } catch (_:SecurityException) {return fail("Permissão retirada ou GPS bloqueado pelo Android. Distância preservada; retome pelo app.")}
        catch (_:Exception) {return fail("GPS interrompido. Distância preservada; tente retomar pelo app.")}
        return START_STICKY
    }
    private fun gpsEnabled()=runCatching {manager.isProviderEnabled(LocationManager.GPS_PROVIDER)}.getOrDefault(false)
    private fun accept(point:Location) {
        if(!state.value.active) return
        val now=SystemClock.elapsedRealtime()
        val result=accumulator.accept(GpsFix(point.latitude,point.longitude,
            if(point.hasAccuracy()) point.accuracy.toDouble() else Double.POSITIVE_INFINITY,
            point.elapsedRealtimeNanos/1_000_000),now)
        if(result.usable) {
            val current=state.value
            publish(current.copy(meters=current.meters+result.added,lastFixElapsed=point.elapsedRealtimeNanos/1_000_000,
                signal=GpsSignal.GOOD,hasGap=current.hasGap || result.gap,durationMillis=current.duration(now)))
            notifyProgress()
        } else if(point.hasAccuracy() && point.accuracy>35f && state.value.signal!=GpsSignal.LOST) {
            state.value=state.value.copy(signal=GpsSignal.WEAK)
            notifyProgress()
        }
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
            GpsSignal.WEAK -> "Sinal impreciso · distância preservada"
            GpsSignal.DISABLED -> "Localização desligada · distância preservada"
            GpsSignal.LOST -> "Sinal GPS perdido · distância preservada"
            else -> "Buscando sinal GPS"
        }
        val text=label+" · %.3f km".format(java.util.Locale.US,state.value.meters/1000)
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
        listener?.let {runCatching {manager.removeUpdates(it)}}
        listener=null;accumulator.breakSegment();running=false
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
