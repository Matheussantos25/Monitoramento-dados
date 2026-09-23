package com.matheussantos.solem.ui

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner

/** Foreground-only opt-in distance measurement. Coordinates never leave this composable. */
@Composable fun GpsDistanceTracker(onDistance: (Double) -> Unit) {
    val context = LocalContext.current
    val owner = LocalLifecycleOwner.current
    val manager = remember { context.getSystemService(Context.LOCATION_SERVICE) as LocationManager }
    fun permitted() = listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        .any { ContextCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED }
    var allowed by remember { mutableStateOf(permitted()) }
    var active by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var meters by remember { mutableDoubleStateOf(0.0) }
    var last by remember { mutableStateOf<Location?>(null) }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        allowed = result.values.any { it }
        active = allowed
        if (!allowed) message = "Localização não autorizada. Informe a distância manualmente."
    }
    DisposableEffect(owner) {
        val observer = LifecycleEventObserver { _, event -> if (event == Lifecycle.Event.ON_STOP) active = false }
        owner.lifecycle.addObserver(observer)
        onDispose { owner.lifecycle.removeObserver(observer) }
    }
    DisposableEffect(active, allowed) {
        val listener = LocationListener { point ->
            if (!point.hasAccuracy() || point.accuracy > 50f) return@LocationListener
            val previous = last
            if (previous != null) {
                val step = previous.distanceTo(point).toDouble()
                if (step in 2.0..250.0) {
                    meters += step
                    onDistance(meters / 1000.0)
                }
            }
            last = point
        }
        if (active && allowed) {
            try {
                val providers = listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)
                    .filter { manager.isProviderEnabled(it) }
                if (providers.isEmpty()) message = "Ative a localização no aparelho ou informe a distância manualmente."
                providers.forEach { manager.requestLocationUpdates(it, 1000L, 5f, listener) }
            } catch (_: SecurityException) { message = "A permissão de localização foi retirada."; active = false }
            catch (_: IllegalArgumentException) { message = "GPS indisponível neste aparelho."; active = false }
        }
        onDispose { manager.removeUpdates(listener) }
    }
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("Distância por GPS (opcional)", style = MaterialTheme.typography.titleSmall)
        Text("Usado somente com esta tela aberta. Salva apenas a distância, nunca o trajeto ou coordenadas.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = {
                if (active) active = false else {
                    meters = 0.0; last = null; message = null
                    if (permitted()) { allowed = true; active = true }
                    else launcher.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
                }
            }) { Text(if (active) "Parar GPS" else "Iniciar GPS") }
            Text("%.3f km".format(java.util.Locale.US, meters / 1000.0), modifier = Modifier.padding(top = 12.dp))
        }
        message?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error) }
    }
}
