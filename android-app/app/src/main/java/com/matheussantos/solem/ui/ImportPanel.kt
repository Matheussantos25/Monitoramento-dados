package com.matheussantos.solem.ui
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.data.model.*
import java.time.LocalTime
import java.time.ZoneOffset

@Composable fun ImportPanel(rows: List<TrainingRecord>, catalog: Catalog, busy: Boolean, save: (List<TrainingMutation>, () -> Unit) -> Unit) {
    var input by remember { mutableStateOf("") }
    var preview by remember { mutableStateOf<ImportResult?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    OutlinedTextField(input, { input = it; preview = null; error = null }, modifier = Modifier.fillMaxWidth(),
        label = { Text("Cole o resultado do simulado com o JSON") }, minLines = 5, maxLines = 12)
    Button(onClick = {
        try {
            preview = SimulationImport.parse(input, catalog.subjects, catalog.topics, LocalTime.now(ZoneOffset.ofHours(-3)).withNano(0).toString())
            error = null
        } catch (e: Exception) { preview = null; error = e.message ?: "Formato inválido." }
    }, enabled = !busy) { Text("Validar e visualizar") }
    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    preview?.let { p ->
        val duplicate = rows.any { it.extra("importacao_id") == p.id }
        Panel("Prévia: ${p.questionCount} questões • ${p.rows.size} registros") {
            p.warnings.forEach { Text(it) }
            p.rows.forEach { r -> Text("${r.exercicio}\n${r.extras["topico_edital"]}\n${r.repeticoes} questões • ${r.durationMinutes} minutos") }
            if (duplicate) Text("Este simulado já consta no histórico.")
            Button(onClick = { save(p.rows) { input = ""; preview = null } }, enabled = !busy && !duplicate) { Text(if (busy) "Importando…" else "Confirmar importação") }
        }
    }
}
