package com.matheussantos.solem.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.domain.Catalog
import com.matheussantos.solem.domain.sleepMinutes
import com.matheussantos.solem.domain.today
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

private val meals = listOf("Café da manhã", "Lanche da manhã", "Almoço", "Lanche da tarde", "Jantar", "Ceia", "Outra")
private val clockFormat = DateTimeFormatter.ofPattern("HH:mm:ss")
private fun currentTime(): String = LocalTime.now(ZoneOffset.ofHours(-3)).format(clockFormat)
private fun foods(row: HealthEntry, key: String): String = (row.details[key] as? JsonArray)
    ?.mapNotNull { (it as? JsonPrimitive)?.content }?.joinToString(", ").orEmpty()
private fun splitFoods(text: String) = text.split(",").map { it.trim() }.filter { it.isNotBlank() }

@Composable fun HealthPage(catalog: Catalog, vm: WorkspaceViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    var selected by rememberSaveable { mutableIntStateOf(0) }
    var dayText by rememberSaveable { mutableStateOf(today().toString()) }
    var deleting by remember { mutableStateOf<HealthEntry?>(null) }
    val day = runCatching { LocalDate.parse(dayText) }.getOrNull()
    val rows = if (day == null) emptyList() else state.healthEntries.filter { it.day == day.toString() }
    val dayMeals = rows.filter { it.kind == "meal" }
    val water = rows.filter { it.kind == "water" }.sumOf {
        it.number("volume_ml").toInt() * it.number("quantidade").toInt()
    }
    val weight = rows.firstOrNull { it.kind == "weight" }
    val sleep = rows.firstOrNull { it.kind == "sleep" }
    var requested by remember { mutableStateOf(false) }
    LaunchedEffect(state.busy) {
        if (!state.busy && !requested) { requested = true; vm.loadHealth() }
    }
    Page("Saúde") {
        Text("Seu diário privado de alimentação, água, peso, sono e fotos. Os registros antigos em treinos não foram migrados.",
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        Field("Dia em foco (AAAA-MM-DD)", dayText) { dayText = it }
        if (day == null) Text("Informe uma data válida.", color = MaterialTheme.colorScheme.error)
        else Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            listOf("Refeições: ${dayMeals.size}", "Água: $water ml",
                "Peso: ${weight?.text("kg")?.ifBlank { "—" } ?: "—"} kg",
                "Sono: ${sleep?.text("duracao_min")?.ifBlank { "—" } ?: "—"} min")
                .forEach { Text(it, color = MaterialTheme.colorScheme.primary) }
        }
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        if (state.failed) Text(state.message ?: "Falha no diário. Confira a sessão e a migração 20260923_health_diary.sql.",
            color = MaterialTheme.colorScheme.error)
        TextButton(onClick = vm::loadHealth, enabled = !state.busy) { Text("Atualizar diário") }
        val tabs = listOf("Alimentação", "Água", "Peso", "Sono", "Fotos")
        ScrollableTabRow(selectedTabIndex = selected) {
            tabs.forEachIndexed { index, name -> Tab(selected == index, onClick = { selected = index }, text = { Text(name) }) }
        }
        if (day != null) when (selected) {
            0 -> {
                MealForm(day, catalog, state.busy, vm)
                if (dayMeals.isEmpty()) Text("Nenhuma refeição registrada neste dia.")
                dayMeals.sortedBy { it.loggedAt }.forEach { row ->
                    Panel("${row.text("tipo_refeicao")} · ${row.loggedAt.take(5)}") {
                        Text("Saudáveis: ${foods(row, "saudaveis").ifBlank { "—" }}")
                        Text("Ocasionais: ${foods(row, "ocasionais").ifBlank { "—" }}")
                        TextButton(onClick = { deleting = row }) { Text("Remover refeição") }
                    }
                }
            }
            1 -> {
                WaterForm(day, water, state.busy, vm)
                rows.filter { it.kind == "water" }.sortedBy { it.loggedAt }.forEach { row ->
                    Panel("${row.loggedAt.take(5)} · ${row.text("recipiente")}") {
                        Text("${row.text("quantidade")} × ${row.text("volume_ml")} ml")
                        TextButton(onClick = { deleting = row }) { Text("Remover registro") }
                    }
                }
            }
            2 -> DailyWeight(day, weight, state.busy, vm)
            3 -> DailySleep(day, sleep, state.busy, vm)
            4 -> ProgressPhotosPage(vm, day)
        }
    }
    deleting?.let { row ->
        AlertDialog(onDismissRequest = { deleting = null }, title = { Text("Remover registro privado?") },
            text = { Text("Esta ação não pode ser desfeita.") },
            confirmButton = { TextButton(onClick = { vm.deleteHealth(row.id); deleting = null }) { Text("Remover") } },
            dismissButton = { TextButton(onClick = { deleting = null }) { Text("Cancelar") } })
    }
}

@Composable private fun MealForm(day: LocalDate, catalog: Catalog, busy: Boolean, vm: WorkspaceViewModel) {
    var kind by rememberSaveable { mutableStateOf("Almoço") }
    var time by rememberSaveable { mutableStateOf(currentTime()) }
    var healthy by rememberSaveable { mutableStateOf("") }
    var occasional by rememberSaveable { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    Choice("Tipo de refeição", kind, meals) { kind = it }
    Field("Horário (HH:MM:SS)", time) { time = it }
    MultiChoice("Alimentos saudáveis / habituais", splitFoods(healthy), catalog.list("ALIMENTOS_SAUDAVEIS").sorted()) {
        healthy = it.joinToString(", ")
    }
    Field("Outros saudáveis, separados por vírgula", healthy) { healthy = it }
    MultiChoice("Besteiras / ocasionais", splitFoods(occasional), catalog.list("ALIMENTOS_BESTEIROL").sorted()) {
        occasional = it.joinToString(", ")
    }
    Field("Outros ocasionais, separados por vírgula", occasional) { occasional = it }
    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    Button(onClick = {
        if (splitFoods(healthy).isEmpty() && splitFoods(occasional).isEmpty()) error = "Informe ao menos um alimento."
        else try {
            val checked = LocalTime.parse(time).format(clockFormat)
            val data = buildJsonObject {
                put("tipo_refeicao", kind)
                put("saudaveis", buildJsonArray { splitFoods(healthy).forEach { add(JsonPrimitive(it)) } })
                put("ocasionais", buildJsonArray { splitFoods(occasional).forEach { add(JsonPrimitive(it)) } })
            }
            error = null
            vm.saveHealth(day.toString(), checked, "meal", data)
        } catch (_: Exception) { error = "Confira o horário da refeição." }
    }, enabled = !busy) { Text("Salvar refeição privada") }
}

@Composable private fun WaterForm(day: LocalDate, total: Int, busy: Boolean, vm: WorkspaceViewModel) {
    var container by rememberSaveable { mutableStateOf("Garrafa") }
    var volume by rememberSaveable { mutableStateOf("750") }
    var count by rememberSaveable { mutableStateOf("1") }
    var time by rememberSaveable { mutableStateOf(currentTime()) }
    var error by remember { mutableStateOf<String?>(null) }
    Choice("Recipiente", container, listOf("Garrafa", "Copo")) { container = it }
    Field("Volume por recipiente (ml)", volume, true) { volume = it }
    Field("Quantidade consumida", count, true) { count = it }
    Field("Horário (HH:MM:SS)", time) { time = it }
    Text("Este registro: ${(volume.toIntOrNull() ?: 0) * (count.toIntOrNull() ?: 0)} ml · total do dia: $total ml")
    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    Button(onClick = {
        val size = volume.toIntOrNull()
        val amount = count.toIntOrNull()
        val checked = runCatching { LocalTime.parse(time).format(clockFormat) }.getOrNull()
        if (size == null || size !in 50..5000 || amount == null || amount !in 1..50 || checked == null)
            error = "Informe volume de 50 a 5000 ml, quantidade de 1 a 50 e horário válido."
        else {
            error = null
            vm.saveHealth(day.toString(), checked, "water", buildJsonObject {
                put("recipiente", container); put("volume_ml", size); put("quantidade", amount)
            })
        }
    }, enabled = !busy) { Text("Adicionar água") }
}

@Composable private fun DailyWeight(day: LocalDate, previous: HealthEntry?, busy: Boolean, vm: WorkspaceViewModel) {
    var value by rememberSaveable(day, previous?.id) { mutableStateOf(previous?.text("kg").orEmpty()) }
    var error by remember { mutableStateOf<String?>(null) }
    Text("Uma medida por dia. Salvar novamente atualiza a anterior.")
    Field("Peso corporal (kg)", value, true) { value = it }
    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    Button(onClick = {
        val kg = value.replace(',', '.').toDoubleOrNull()
        if (kg == null || !kg.isFinite() || kg !in 1.0..500.0) error = "Informe um peso entre 1 e 500 kg."
        else { error = null; vm.saveHealth(day.toString(), "00:00:00", "weight",
            buildJsonObject { put("kg", kg) }, previous?.id) }
    }, enabled = !busy) { Text(if (previous == null) "Salvar peso" else "Atualizar peso") }
}

@Composable private fun DailySleep(day: LocalDate, previous: HealthEntry?, busy: Boolean, vm: WorkspaceViewModel) {
    var bed by rememberSaveable(day, previous?.id) { mutableStateOf(previous?.text("dormir")?.ifBlank { "23:00" } ?: "23:00") }
    var wake by rememberSaveable(day, previous?.id) { mutableStateOf(previous?.text("acordar")?.ifBlank { "07:00" } ?: "07:00") }
    var error by remember { mutableStateOf<String?>(null) }
    Text("O dia em foco é o dia em que você acordou. Um registro por dia.")
    Field("Dormiu (HH:MM)", bed) { bed = it }
    Field("Acordou (HH:MM)", wake) { wake = it }
    error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    Button(onClick = {
        try {
            val minutes = sleepMinutes(bed, wake)
            error = null
            vm.saveHealth(day.toString(), "00:00:00", "sleep", buildJsonObject {
                put("dormir", bed); put("acordar", wake); put("duracao_min", minutes)
            }, previous?.id)
        } catch (_: Exception) { error = "Confira os horários; duração máxima de 16 horas." }
    }, enabled = !busy) { Text(if (previous == null) "Salvar sono" else "Atualizar sono") }
    Text("Duração calculada dos horários, sem monitoramento automático.",
        color = MaterialTheme.colorScheme.onSurfaceVariant)
}
