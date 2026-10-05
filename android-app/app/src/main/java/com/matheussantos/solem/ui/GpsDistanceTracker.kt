package com.matheussantos.solem.ui

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.SystemClock
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.domain.clockText
import kotlinx.coroutines.delay
import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

/** Foreground service owns the location session while the display is locked. */
@Composable fun GpsDistanceTracker(onDistance: (Double) -> Unit, onFinished: (Double, Long) -> Unit) {
    val context = LocalContext.current
    val tracking by WalkLocationService.state.collectAsStateWithLifecycle()
    var startedHere by rememberSaveable { mutableStateOf(false) }
    var consumedSession by rememberSaveable { mutableStateOf(0L) }
    var elapsed by remember { mutableStateOf(0L) }
    val finishedCallback by rememberUpdatedState(onFinished)
    fun permitted() = listOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION)
        .any { ContextCompat.checkSelfPermission(context, it) == PackageManager.PERMISSION_GRANTED }
    var message by remember { mutableStateOf<String?>(null) }
    fun start() {
        message = null
        startedHere = true
        try {
            ContextCompat.startForegroundService(context, Intent(context, WalkLocationService::class.java).setAction(WalkLocationService.START))
        } catch (_: Exception) { message = "Não foi possível iniciar o GPS. Verifique a permissão e tente novamente." }
    }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
        if (result.values.any { it }) start() else message = "Localização não autorizada. Informe a distância manualmente."
    }
    var notificationAllowed by remember {mutableStateOf(Build.VERSION.SDK_INT<33 || ContextCompat.checkSelfPermission(context,
        Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED)}
    val notificationLauncher=rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {notificationAllowed=it}
    LaunchedEffect(tracking.meters) { if (tracking.active || startedHere) onDistance(tracking.meters / 1000.0) }
    LaunchedEffect(tracking.active, tracking.startedAtMillis) {
        if (tracking.active) {
            startedHere = true
            while (true) {
                elapsed = (SystemClock.elapsedRealtime() - tracking.startedElapsedMillis).coerceAtLeast(0)
                delay(250)
            }
        } else {
            elapsed = tracking.durationMillis
            if (startedHere && tracking.error == null && tracking.startedAtMillis > 0 && consumedSession != tracking.startedAtMillis) {
                consumedSession = tracking.startedAtMillis
                finishedCallback(tracking.meters / 1000.0, tracking.durationMillis / 1000)
                startedHere = false
            }
        }
    }
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text("Distância por GPS (opcional)", style = MaterialTheme.typography.titleSmall)
        Text("Continua com a tela bloqueada enquanto a notificação estiver ativa. Usa distância e duração, nunca o trajeto ou coordenadas. Pare antes de salvar o treino.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(onClick = {
                if (tracking.active) context.startService(Intent(context, WalkLocationService::class.java).setAction(WalkLocationService.STOP)) else {
                    if (permitted()) start()
                    else launcher.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION))
                }
            }) { Text(if (tracking.active) "Parar GPS" else "Iniciar GPS") }
            Text("%.3f km".format(java.util.Locale.US, tracking.meters / 1000.0), modifier = Modifier.padding(top = 12.dp))
        }
        Text("Duração: ${clockText(elapsed / 1000)}")
        if(Build.VERSION.SDK_INT>=33 && !notificationAllowed) {
            Text("Ative a notificação para acessar o botão Parar GPS na tela bloqueada. Sem ela, pare pelo app.",style=MaterialTheme.typography.bodySmall)
            TextButton({notificationLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)}) {Text("Ativar notificação do GPS")}
        }
        if (tracking.startedAtMillis > 0) Text("Iniciado às " + Instant.ofEpochMilli(tracking.startedAtMillis)
            .atOffset(ZoneOffset.ofHours(-3)).format(DateTimeFormatter.ofPattern("HH:mm:ss")), style = MaterialTheme.typography.bodySmall)
        (message ?: tracking.error)?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error) }
    }
}
