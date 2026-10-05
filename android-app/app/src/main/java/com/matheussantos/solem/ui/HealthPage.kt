package com.matheussantos.solem.ui

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.Alignment
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChevronLeft
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.domain.Catalog
import com.matheussantos.solem.domain.sleepMinutes
import com.matheussantos.solem.domain.today
import com.matheussantos.solem.domain.*
import androidx.compose.ui.platform.LocalContext
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.decodeFromJsonElement
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

private val clockFormat = DateTimeFormatter.ofPattern("HH:mm:ss")
private fun currentTime(): String = LocalTime.now(ZoneOffset.ofHours(-3)).format(clockFormat)
private fun foods(row: HealthEntry, key: String): String = (row.details[key] as? JsonArray)
    ?.mapNotNull { (it as? JsonPrimitive)?.content }?.joinToString(", ").orEmpty()
private fun splitFoods(text: String) = text.split(",").map { it.trim() }.filter { it.isNotBlank() }

@OptIn(ExperimentalMaterial3Api::class,ExperimentalLayoutApi::class)
@Composable fun HealthPage(catalog: Catalog, vm: WorkspaceViewModel,initialSection:Int=-1) {
    val context=LocalContext.current
    val state by vm.state.collectAsStateWithLifecycle()
    var selected by rememberSaveable(initialSection) { mutableIntStateOf(initialSection.coerceIn(-1,4)) }
    var dayText by rememberSaveable { mutableStateOf(today().toString()) }
    var deleting by remember { mutableStateOf<HealthEntry?>(null) }
    var editingId by remember { mutableStateOf<String?>(null) }
    var pickingDate by remember { mutableStateOf(false) }
    val day = runCatching { LocalDate.parse(dayText) }.getOrNull()
    val rows = if (day == null) emptyList() else state.healthEntries.filter { it.day == day.toString() }
    val dayMeals = rows.filter { it.kind == "meal" }
    val water = rows.filter { it.kind == "water" }.sumOf {
        it.number("volume_ml").toInt() * it.number("quantidade").toInt()
    }
    val weight = rows.firstOrNull { it.kind == "weight" }
    val sleep = rows.firstOrNull { it.kind == "sleep" }
    LaunchedEffect(dayText) { editingId=null }
    Page("Saúde") {
        Text("Alimentação, hidratação, descanso e evolução. Um diário privado, no seu ritmo.",
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
            IconButton({day?.let {dayText=it.minusDays(1).toString()}}) {Icon(Icons.Outlined.ChevronLeft,"Dia anterior")}
            TextButton({pickingDate=true},modifier=Modifier.weight(1f)) {
                Icon(Icons.Outlined.CalendarMonth,null);Spacer(Modifier.width(8.dp))
                Text(day?.format(DateTimeFormatter.ofPattern("dd MMM yyyy",java.util.Locale.forLanguageTag("pt-BR"))) ?: dayText)
            }
            IconButton({day?.let {dayText=it.plusDays(1).toString()}}) {Icon(Icons.Outlined.ChevronRight,"Próximo dia")}
        }
        if(day!=today()) TextButton({dayText=today().toString()}) {Text("Voltar para hoje")}
        if (day == null) Text("Informe uma data válida.", color = MaterialTheme.colorScheme.error)
        if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        if (state.failed) Text(state.message ?: "Falha no diário. Confira a sessão e a migração 20260923_health_diary.sql.",
            color = MaterialTheme.colorScheme.error)
        TextButton(onClick = vm::loadHealth, enabled = !state.busy) { Text("Atualizar diário") }
        val tabs = listOf("Alimentação", "Água", "Peso", "Sono", "Fotos")
        FlowRow(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            FilterChip(selected=selected==-1,onClick={selected=-1},label={Text("Resumo")})
            tabs.forEachIndexed { index,name -> FilterChip(selected=selected==index,onClick={selected=index},label={Text(name)}) }
        }
        if (day != null) when (selected) {
            -1 -> HealthSummary(rows,state.healthLoaded && !state.healthFailed,state.busy,{selected=it},{volume ->
                vm.saveHealth(day.toString(),currentTime(),"water",buildJsonObject {
                    put("recipiente","Registro rápido");put("volume_ml",volume);put("quantidade",1)
                })
            })
            0 -> {
                val references: List<MealReference> = remember {
                    mealJson.decodeFromString(contextAssets(context))
                }
                val calculated=dayMeals.mapNotNull { row ->
                    runCatching { row.details["nutrition"]?.let { mealJson.decodeFromJsonElement<MealEstimate>(it) }
                        ?.let { calculateMeal(it.items,references) } }.getOrNull()
                }
                if(calculated.isNotEmpty()) Panel("Nutrição registrada no dia") {
                    val totals=MealNutrients(calculated.sumOf { it.totals.kcal },calculated.sumOf { it.totals.protein },
                        calculated.sumOf { it.totals.carbs },calculated.sumOf { it.totals.fat },calculated.sumOf { it.totals.fiber })
                    MealNutritionSummary(MealEstimate(emptyList(),totals,calculated.sumOf { it.missing },
                        calculated.size==dayMeals.size && calculated.all { it.complete }))
                    Text("${calculated.size} de ${dayMeals.size} refeição(ões) com cálculo. Registros manuais não estão incluídos.")
                }
                MealForm(day, catalog, state.busy, vm)
                if (dayMeals.isEmpty()) Text("Nenhuma refeição registrada neste dia.")
                dayMeals.sortedBy { it.loggedAt }.forEach { row ->
                    Panel("${row.text("tipo_refeicao")} · ${row.loggedAt.take(5)}") {
                        Text("${if(row.details["nutrition"]!=null) "Confirmados" else "Habituais"}: ${foods(row, "saudaveis").ifBlank { "—" }}")
                        Text("Ocasionais: ${foods(row, "ocasionais").ifBlank { "—" }}")
                        val nutrition=runCatching { row.details["nutrition"]?.let { mealJson.decodeFromJsonElement<MealEstimate>(it) } }.getOrNull()
                        nutrition?.let { runCatching { calculateMeal(it.items,references) }.getOrNull()?.let { checked -> MealNutritionSummary(checked) } }
                        TextButton(onClick = { editingId = if (editingId == row.id) null else row.id }) {
                            Text(if (editingId == row.id) "Fechar edição" else "Editar refeição")
                        }
                        if (editingId == row.id) {
                            if(nutrition!=null) key(row.id) { MealReview(day,catalog,vm,references,nutrition.items,state.busy,row,
                                saved={editingId=null}) }
                            else MealForm(day, catalog, state.busy, vm, row)
                        }
                        TextButton(onClick = { deleting = row }) { Text("Remover refeição") }
                    }
                }
            }
            1 -> {
                WaterForm(day, water, state.busy, vm)
                rows.filter { it.kind == "water" }.sortedBy { it.loggedAt }.forEach { row ->
                    Panel("${row.loggedAt.take(5)} · ${row.text("recipiente")}") {
                        Text("${row.text("quantidade")} × ${row.text("volume_ml")} ml")
                        TextButton(onClick = { editingId = if (editingId == row.id) null else row.id }) {
                            Text(if (editingId == row.id) "Fechar edição" else "Editar água")
                        }
                        if (editingId == row.id) WaterForm(day, water, state.busy, vm, row)
                        TextButton(onClick = { deleting = row }) { Text("Remover registro") }
                    }
                }
            }
            2 -> {
                DailyWeight(day, weight, state.busy, vm)
                PrivateWeightLine(state.healthEntries)
            }
            3 -> DailySleep(day, sleep, state.busy, vm)
            4 -> ProgressPhotosPage(vm, day)
        }
    }
    if(pickingDate) {
        val picker=rememberDatePickerState(initialSelectedDateMillis=(day ?: today()).atStartOfDay().toInstant(ZoneOffset.UTC).toEpochMilli())
        DatePickerDialog(onDismissRequest={pickingDate=false},confirmButton={TextButton({
            picker.selectedDateMillis?.let {dayText=java.time.Instant.ofEpochMilli(it).atOffset(ZoneOffset.UTC).toLocalDate().toString()}
            pickingDate=false
        }) {Text("Selecionar")}},dismissButton={TextButton({pickingDate=false}) {Text("Cancelar")}}) { DatePicker(state=picker) }
    }
    deleting?.let { row ->
        AlertDialog(onDismissRequest = { deleting = null }, title = { Text("Remover registro privado?") },
            text = { Text("Esta ação não pode ser desfeita.") },
            confirmButton = { TextButton(onClick = { vm.deleteHealth(row.id); deleting = null }) { Text("Remover") } },
            dismissButton = { TextButton(onClick = { deleting = null }) { Text("Cancelar") } })
    }
}

@Composable private fun MealForm(day: LocalDate, catalog: Catalog, busy: Boolean, vm: WorkspaceViewModel,
                                 previous: HealthEntry? = null) {
    var kind by rememberSaveable(previous?.id) { mutableStateOf(previous?.text("tipo_refeicao")?.ifBlank { "Almoço" } ?: "Almoço") }
    var time by rememberSaveable(previous?.id) { mutableStateOf(previous?.loggedAt ?: currentTime()) }
    var healthy by rememberSaveable(previous?.id) { mutableStateOf(previous?.let { foods(it, "saudaveis") } ?: "") }
    var occasional by rememberSaveable(previous?.id) { mutableStateOf(previous?.let { foods(it, "ocasionais") } ?: "") }
    var error by remember { mutableStateOf<String?>(null) }
    Choice("Tipo de refeição", kind, (catalog.mealTypes + kind).distinct()) { kind = it }
    Field("Horário (HH:MM:SS)", time) { time = it }
    MultiChoice("Alimentos habituais", splitFoods(healthy), catalog.mealFoods(kind, splitFoods(healthy))) {
        healthy = it.joinToString(", ")
    }
    Field("Outros habituais, separados por vírgula", healthy) { healthy = it }
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
            vm.saveHealth(day.toString(), checked, "meal", data, previous?.id)
        } catch (_: Exception) { error = "Confira o horário da refeição." }
    }, enabled = !busy) { Text(if (previous == null) "Salvar refeição privada" else "Salvar edição da refeição") }
}

private fun contextAssets(context: android.content.Context) = context.assets.open("nutrition_catalog.json").bufferedReader().use { it.readText() }

@Composable private fun WaterForm(day: LocalDate, total: Int, busy: Boolean, vm: WorkspaceViewModel,
                                  previous: HealthEntry? = null) {
    var container by rememberSaveable(previous?.id) { mutableStateOf(previous?.text("recipiente")?.ifBlank { "Garrafa" } ?: "Garrafa") }
    var volume by rememberSaveable(previous?.id) { mutableStateOf(previous?.text("volume_ml")?.ifBlank { "750" } ?: "750") }
    var count by rememberSaveable(previous?.id) { mutableStateOf(previous?.text("quantidade")?.ifBlank { "1" } ?: "1") }
    var time by rememberSaveable(previous?.id) { mutableStateOf(previous?.loggedAt ?: currentTime()) }
    var error by remember { mutableStateOf<String?>(null) }
    Choice("Recipiente", container, (listOf("Garrafa", "Copo") + container).distinct()) { container = it }
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
            }, previous?.id)
        }
    }, enabled = !busy) { Text(if (previous == null) "Adicionar água" else "Salvar edição da água") }
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
    }, enabled = !busy) { Text(if (previous == null) "Salvar peso" else "Salvar edição do peso") }
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
    }, enabled = !busy) { Text(if (previous == null) "Salvar sono" else "Salvar edição do sono") }
    Text("Duração calculada dos horários, sem monitoramento automático.",
        color = MaterialTheme.colorScheme.onSurfaceVariant)
}
