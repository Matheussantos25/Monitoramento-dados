package com.matheussantos.solem.ui

import android.graphics.BitmapFactory
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.data.model.ProgressPhoto
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import java.time.LocalDate

@Composable fun ProgressPhotosPage(vm: WorkspaceViewModel, day: LocalDate) {
    val state by vm.state.collectAsStateWithLifecycle()
    var kind by remember { mutableStateOf("face") }
    var pending by remember { mutableStateOf(false) }
    var deleting by remember { mutableStateOf<ProgressPhoto?>(null) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null && pending) vm.uploadPhoto(day.toString(), kind, uri)
        pending = false
    }
    var requested by remember { mutableStateOf(false) }
    LaunchedEffect(state.busy) {
        if (!state.busy && !requested) { requested = true; vm.loadPhotos() }
    }
    Text("Fotos opcionais de rosto e corpo, privadas por conta. O app remove metadados, inclusive localização, antes do envio.",
        color = MaterialTheme.colorScheme.onSurfaceVariant)
    Choice("Tipo de foto", if (kind == "face") "Rosto" else "Corpo", listOf("Rosto", "Corpo")) {
        kind = if (it == "Rosto") "face" else "body"
    }
    val current = state.photos.firstOrNull { it.day == day.toString() && it.kind == kind }
    Button(onClick = { pending = true; picker.launch(arrayOf("image/*")) }, enabled = !state.busy && current == null) {
        Text(if (current == null) "Adicionar foto de ${if (kind == "face") "rosto" else "corpo"}" else "Foto já registrada neste dia")
    }
    Text("Uma foto por tipo e dia. Para substituir, remova a anterior primeiro.", style = MaterialTheme.typography.bodySmall)
    if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    TextButton(onClick = vm::loadPhotos, enabled = !state.busy) { Text("Atualizar fotos") }
    if (state.failed) Text(state.message ?: "Falha ao carregar fotos privadas.", color = MaterialTheme.colorScheme.error)
    if (state.photos.isEmpty()) {
        Text("Sua linha do tempo começa com a primeira foto. Ative a migração 20260923_health_photos.sql no Supabase se necessário.")
        return
    }
    val days = state.photos.map { it.day }.distinct().sorted()
    var from by remember { mutableStateOf("") }
    var to by remember { mutableStateOf("") }
    val start = from.takeIf { it in days } ?: days.first()
    val end = to.takeIf { it in days } ?: days.last()
    Text("Comparar evolução", style = MaterialTheme.typography.titleLarge)
    Choice("Data inicial", start, days) { from = it }
    Choice("Data final", end, days) { to = it }
    val selected = listOf("face", "body").flatMap { category ->
        listOfNotNull(state.photos.firstOrNull { it.day == start && it.kind == category },
            state.photos.firstOrNull { it.day == end && it.kind == category })
    }.distinctBy { it.id }
    LaunchedEffect(selected.map { it.id }, state.busy) {
        if (!state.busy && selected.any { it.id !in state.photoData }) vm.loadPhotoBytes(selected)
    }
    listOf("face" to "Rosto", "body" to "Corpo").forEach { (category, label) ->
        Text(label, style = MaterialTheme.typography.titleMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            for ((caption, date) in listOf("Antes" to start, "Depois" to end)) {
                val photo = state.photos.firstOrNull { it.day == date && it.kind == category }
                Column(Modifier.weight(1f)) {
                    Text("$caption · $date", style = MaterialTheme.typography.labelSmall)
                    PhotoTile(state.photoData[photo?.id], label)
                }
            }
        }
    }
    state.photos.filter { it.day == day.toString() }.forEach { photo ->
        TextButton(onClick = { deleting = photo }) { Text("Remover foto de ${if (photo.kind == "face") "rosto" else "corpo"} deste dia") }
    }
    deleting?.let { photo -> AlertDialog(onDismissRequest = { deleting = null },
        title = { Text("Remover foto permanentemente?") },
        text = { Text("Esta imagem será removida do armazenamento privado. A ação não pode ser desfeita.") },
        confirmButton = { TextButton(onClick = { vm.deletePhoto(photo); deleting = null }) { Text("Remover") } },
        dismissButton = { TextButton(onClick = { deleting = null }) { Text("Cancelar") } }) }
}

@Composable private fun PhotoTile(bytes: ByteArray?, label: String) {
    if (bytes == null) { Text("Sem foto ou carregando…", style = MaterialTheme.typography.bodySmall); return }
    val bitmap = remember(bytes) { BitmapFactory.decodeByteArray(bytes, 0, bytes.size)?.asImageBitmap() }
    if (bitmap == null) Text("Não foi possível abrir a imagem.")
    else Image(bitmap, contentDescription = "Comparação de $label", modifier = Modifier.fillMaxWidth().height(170.dp), contentScale = ContentScale.Crop)
}
