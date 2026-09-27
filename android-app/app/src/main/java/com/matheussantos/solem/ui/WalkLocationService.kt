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
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.matheussantos.solem.MainActivity
import kotlinx.coroutines.flow.MutableStateFlow

data class WalkTracking(val active: Boolean = false, val meters: Double = 0.0, val error: String? = null)

/** Started while the app is visible. Neither coordinates nor route are persisted. */
class WalkLocationService : Service() {
    companion object {
        const val START = "solem.gps.START"
        const val STOP = "solem.gps.STOP"
        private const val CHANNEL = "solem_walk_tracking"
        private const val NOTIFICATION = 104
        val state = MutableStateFlow(WalkTracking())
    }

    private lateinit var manager: LocationManager
    private var previous: Location? = null
    private var listener: LocationListener? = null
    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        manager = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(
            NotificationChannel(CHANNEL, "Medição de caminhada e corrida", NotificationManager.IMPORTANCE_LOW))
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == STOP) {
            stopTracking()
            return START_NOT_STICKY
        }
        if (intent?.action != START || state.value.active) return START_NOT_STICKY
        val allowed = listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
            .any { ContextCompat.checkSelfPermission(this, it) == PackageManager.PERMISSION_GRANTED }
        if (!allowed) return fail("Permissão de localização necessária.")
        try {
            if (Build.VERSION.SDK_INT >= 29) startForeground(NOTIFICATION, notification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
            else startForeground(NOTIFICATION, notification())
            state.value = WalkTracking(active = true)
            previous = null
            val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER).filter { manager.isProviderEnabled(it) }
            if (providers.isEmpty()) return fail("Ative a localização do aparelho.")
            val callback = LocationListener { point -> accept(point) }
            listener = callback
            providers.forEach { manager.requestLocationUpdates(it, 1000L, 5f, callback) }
        } catch (_: SecurityException) { return fail("Permissão de localização retirada ou serviço bloqueado.") }
        catch (_: Exception) { return fail("GPS indisponível. Informe a distância manualmente.") }
        return START_NOT_STICKY
    }

    private fun accept(point: Location) {
        if (!point.hasAccuracy() || point.accuracy > 50f) return
        val last = previous
        if (last != null) {
            val step = last.distanceTo(point).toDouble()
            val seconds = (point.elapsedRealtimeNanos - last.elapsedRealtimeNanos) / 1e9
            if (step in 2.0..250.0 && seconds > 0 && step / seconds <= 8.0) {
                state.value = state.value.copy(meters = state.value.meters + step)
                (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager).notify(NOTIFICATION, notification())
            }
        }
        previous = point
    }

    private fun notification(): Notification {
        val open = PendingIntent.getActivity(this, 0, Intent(this, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val stop = PendingIntent.getService(this, 1, Intent(this, WalkLocationService::class.java).setAction(STOP), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        return NotificationCompat.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentTitle("Solem · caminhada/corrida")
            .setContentText("GPS ativo · %.3f km. Toque para voltar ao treino.".format(java.util.Locale.US, state.value.meters / 1000.0))
            .setContentIntent(open).addAction(android.R.drawable.ic_media_pause, "Parar GPS", stop)
            .setOngoing(true).build()
    }

    private fun fail(text: String): Int {
        state.value = state.value.copy(active = false, error = text)
        stopTracking()
        return START_NOT_STICKY
    }
    private fun stopTracking() {
        listener?.let { manager.removeUpdates(it) }
        listener = null
        previous = null
        state.value = state.value.copy(active = false)
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }
    override fun onDestroy() {
        listener?.let { manager.removeUpdates(it) }
        state.value = state.value.copy(active = false)
        super.onDestroy()
    }
}
