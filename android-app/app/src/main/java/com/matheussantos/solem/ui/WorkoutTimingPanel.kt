package com.matheussantos.solem.ui

import android.media.AudioManager
import android.media.ToneGenerator
import android.os.SystemClock
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.domain.clockText
import com.matheussantos.solem.domain.measuredMillis
import kotlinx.coroutines.delay

@Composable fun WorkoutTimingPanel(exercise: String, restSeconds: Int?, onTime: ((Long) -> Unit)?) {
    key(exercise) {
        var customSeconds by rememberSaveable { mutableStateOf("60") }
        Panel("Medir tempos") {
            ExerciseClock("Cronômetro da atividade", null, onTime)
            HorizontalDivider()
            if (restSeconds == null) Field("Temporizador (segundos)", customSeconds, true) { customSeconds = it }
            else Text("Temporizador vinculado ao descanso entre séries: $restSeconds s.", style = MaterialTheme.typography.bodySmall)
            val total = restSeconds ?: (customSeconds.toIntOrNull() ?: 0).coerceIn(0, 86400)
            ExerciseClock("Contagem regressiva", total, null)
            Text("Inicie cada descanso quando quiser. Os relógios não salvam o treino automaticamente.", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable private fun ExerciseClock(title: String, totalSeconds: Int?, onTime: ((Long) -> Unit)?) {
    var accumulated by rememberSaveable { mutableStateOf(0L) }
    var started by rememberSaveable { mutableStateOf(0L) }
    var running by rememberSaveable { mutableStateOf(false) }
    var complete by rememberSaveable { mutableStateOf(false) }
    var previousTotal by rememberSaveable { mutableStateOf(totalSeconds) }
    var tick by remember { mutableStateOf(SystemClock.elapsedRealtime()) }
    if (previousTotal != totalSeconds) {
        accumulated = 0; running = false; complete = false; previousTotal = totalSeconds
    }
    val used = measuredMillis(accumulated, started, tick, running)
    val remaining = if (totalSeconds == null) used / 1000 else ((totalSeconds * 1000L - used).coerceAtLeast(0) + 999) / 1000
    LaunchedEffect(running, totalSeconds) {
        while (running) {
            tick = SystemClock.elapsedRealtime()
            if (totalSeconds != null && measuredMillis(accumulated, started, tick, true) >= totalSeconds * 1000L) {
                accumulated = totalSeconds * 1000L; running = false; complete = true
                val tone = runCatching { ToneGenerator(AudioManager.STREAM_NOTIFICATION, 60) }.getOrNull()
                try { tone?.startTone(ToneGenerator.TONE_PROP_ACK, 500); delay(600) } finally { tone?.release() }
            }
            delay(200)
        }
    }
    Text(title, style = MaterialTheme.typography.titleSmall)
    Text(clockText(remaining), style = MaterialTheme.typography.displaySmall)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        Button(onClick = {
            val now = SystemClock.elapsedRealtime()
            if (running) { accumulated = measuredMillis(accumulated, started, now, true); running = false }
            else { started = now; tick = now; running = true }
        }, enabled = !complete && (totalSeconds == null || totalSeconds > 0)) { Text(if (running) "Pausar" else "Iniciar") }
        OutlinedButton(onClick = { accumulated = 0; running = false; complete = false }) { Text(if (totalSeconds == null) "Zerar" else "Reiniciar") }
    }
    if (onTime != null) OutlinedButton(onClick = { onTime(accumulated / 1000) }, enabled = !running && accumulated >= 1000 && accumulated <= 86400000) { Text("Usar tempo no registro") }
    if (complete) Text("Tempo concluído! Registre sua série.", color = MaterialTheme.colorScheme.primary)
}
