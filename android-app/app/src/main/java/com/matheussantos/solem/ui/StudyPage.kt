package com.matheussantos.solem.ui

import android.media.ToneGenerator
import android.media.AudioManager
import android.net.Uri
import android.os.SystemClock
import android.widget.VideoView
import android.widget.MediaController
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.TrainingViewModel
import com.matheussantos.solem.R
import kotlinx.coroutines.delay

@Composable fun TimerPanel(fixedSeconds: Int? = null) {
    var mode by rememberSaveable { mutableStateOf("Pomodoro") }
    var minutes by rememberSaveable { mutableStateOf("50") }
    var seconds by rememberSaveable { mutableStateOf("0") }
    var running by rememberSaveable { mutableStateOf(false) }
    var elapsed by rememberSaveable { mutableStateOf(0L) }
    var began by rememberSaveable { mutableStateOf(0L) }
    var tick by remember { mutableStateOf(SystemClock.elapsedRealtime()) }
    var complete by rememberSaveable { mutableStateOf(false) }
    val countdown = fixedSeconds != null || mode == "Pomodoro"
    val total = fixedSeconds ?: ((minutes.toIntOrNull() ?: 0).coerceIn(0, 1440) * 60 + (seconds.toIntOrNull() ?: 0).coerceIn(0, 59))
    val used = elapsed + if (running) (tick-began).coerceAtLeast(0) else 0
    val shown = if (countdown) (total-used/1000).coerceAtLeast(0) else used/1000
    LaunchedEffect(running, total) {
        while (running) {
            tick = SystemClock.elapsedRealtime()
            if (countdown && elapsed + tick - began >= total * 1000L) {
                running = false; elapsed = total * 1000L; complete = true
                val tone = ToneGenerator(AudioManager.STREAM_NOTIFICATION, 70)
                tone.startTone(ToneGenerator.TONE_PROP_ACK, 600)
                delay(700); tone.release()
            }
            delay(200)
        }
    }
    Panel(if (fixedSeconds == null) "Modos de foco" else "AMRAP — 20 minutos") {
        if (fixedSeconds == null && !running && elapsed == 0L) {
            Choice("Protocolo", mode, listOf("Pomodoro", "Cronômetro")) { mode = it }
            if (countdown) { Field("Minutos", minutes, true) { minutes = it }; Field("Segundos", seconds, true) { seconds = it } }
        }
        Text("%02d:%02d:%02d".format(shown/3600, (shown/60)%60, shown%60), style = MaterialTheme.typography.displaySmall)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = {
                if (running) { elapsed += SystemClock.elapsedRealtime()-began; running = false }
                else { began = SystemClock.elapsedRealtime(); tick = began; running = true }
            }, enabled = !complete && (!countdown || total > 0)) { Text(if (running) "Pausar" else "Iniciar") }
            OutlinedButton({ running = false; elapsed = 0; complete = false }) { Text("Reiniciar") }
        }
        if (complete) Text("Ciclo concluído! Registre sua sessão.")
        if (fixedSeconds == null) VideoReward(autoPlay = complete)
    }
}
@Composable fun VideoReward(autoPlay: Boolean) {
    val context = LocalContext.current
    val resourcesByName = mapOf("edit_disciplina" to R.raw.edit_disciplina, "edit_solo" to R.raw.edit_solo,
        "falling" to R.raw.falling, "frase" to R.raw.frase, "makete" to R.raw.makete, "motivation" to R.raw.motivation)
    val videos = resourcesByName.keys.toList()
    var selected by rememberSaveable { mutableStateOf(videos.random()) }
    var play by remember { mutableStateOf(false) }
    LaunchedEffect(autoPlay) { if (autoPlay) play = true }
    Choice("Vídeo motivacional", selected, videos) { selected = it; play = false }
    Row {
        TextButton({ selected = videos.random(); play = false }) { Text("Sortear outro") }
        TextButton({ play = !play }) { Text(if (play) "Fechar vídeo" else "Assistir agora") }
    }
    if (play) key(selected) {
        var player by remember { mutableStateOf<VideoView?>(null) }
        DisposableEffect(Unit) { onDispose { player?.stopPlayback() } }
        AndroidView(factory = {
            VideoView(it).apply {
                player = this
                val id = resourcesByName.getValue(selected)
                setVideoURI(Uri.parse("android.resource://" + context.packageName + "/" + id))
                setMediaController(MediaController(it).also { controls -> controls.setAnchorView(this) })
                setOnPreparedListener { start() }
            }
        }, modifier = Modifier.fillMaxWidth().height(240.dp))
    }
}
@Composable fun StudyPage(rows: List<TrainingRecord>, catalog: Catalog, busy: Boolean, vm: TrainingViewModel) {
    var panel by rememberSaveable { mutableStateOf("Registrar sessão") }
    Page("Central de foco") {
        val next = nextSubject(rows, catalog)
        Panel("Bússola inteligente") {
            Text("Rotação principal: $next\n" + weakestTopic(rows, next, catalog))
            Text("Diário — Português\n" + weakestTopic(rows, "Língua Portuguesa", catalog))
            Text("Diário — Matemática\n" + weakestTopic(rows, "Matemática e Estatística Aplicada", catalog))
        }
        TimerPanel()
        Choice("Ação", panel, listOf("Registrar sessão", "Importar simulado")) { panel = it }
        if (panel == "Registrar sessão") EntryScreen("Estudo", catalog, rows, busy = busy,
            save = { id, value, done -> vm.save(id, value, done) }, embedded = true)
        else ImportPanel(rows, catalog, busy) { values, done -> vm.insertBatch(values, done) }
    }
}
@Composable fun PromptsPage() {
    val context = LocalContext.current
    val clipboard = LocalClipboardManager.current
    val names = remember { context.assets.list("prompts").orEmpty().sorted() }
    var selected by rememberSaveable { mutableStateOf(names.firstOrNull().orEmpty()) }
    val content = remember(selected) { if (selected.isBlank()) "" else context.assets.open("prompts/$selected").bufferedReader().use { it.readText() } }
    Page("Biblioteca de prompts") {
        Choice("Prompt", selected, names) { selected = it }
        Button({ clipboard.setText(AnnotatedString(content)) }, enabled = content.isNotEmpty()) { Text("Copiar prompt") }
        SelectionContainer { Text(content) }
    }
}
