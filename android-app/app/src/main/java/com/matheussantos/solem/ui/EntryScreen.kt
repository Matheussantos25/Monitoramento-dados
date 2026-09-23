package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.*
import com.matheussantos.solem.domain.*
import kotlinx.serialization.json.*
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneOffset

@Composable fun EntryScreen(
    type: String, catalog: Catalog, rows: List<TrainingRecord>, existing: TrainingRecord? = null,
    busy: Boolean = false, save: (Long?, TrainingMutation, () -> Unit) -> Unit,
    batch: (List<TrainingMutation>, () -> Unit) -> Unit = { _, _ -> }, embedded: Boolean = false,
    initialDate: String = today().toString()
) {
    var date by rememberSaveable(initialDate, existing?.id) { mutableStateOf(existing?.data ?: initialDate) }
    var time by rememberSaveable { mutableStateOf(existing?.horario ?: LocalTime.now(ZoneOffset.ofHours(-3)).withNano(0).toString()) }
    var exercise by rememberSaveable { mutableStateOf(existing?.exercicio ?: catalog.exercises.first()) }
    var series by rememberSaveable { mutableStateOf((existing?.series ?: 1).toString()) }
    var reps by rememberSaveable { mutableStateOf((existing?.repeticoes ?: 0).toString()) }
    var load by rememberSaveable { mutableStateOf((existing?.loadKg ?: 0.0).toString()) }
    var duration by rememberSaveable { mutableStateOf((existing?.durationMinutes ?: 0).toString()) }
    var distance by rememberSaveable { mutableStateOf((existing?.distanceKm ?: 0.0).toString()) }
    var rest by rememberSaveable { mutableStateOf((existing?.restSeconds ?: 0).toString()) }
    var iso by rememberSaveable { mutableStateOf(existing?.extra("isometria_segundos")?.ifBlank { "0" } ?: "0") }
    var mood by rememberSaveable { mutableStateOf(existing?.extra("humor")?.ifBlank { "Normal" } ?: "Normal") }
    var rounds by rememberSaveable { mutableStateOf("5") }
    var format by rememberSaveable { mutableStateOf("Exercício isolado") }
    var healthy by rememberSaveable { mutableStateOf(existing?.healthyFood.orEmpty()) }
    var junk by rememberSaveable { mutableStateOf(existing?.junkFood.orEmpty()) }
    var mealType by rememberSaveable { mutableStateOf(existing?.extra("tipo_refeicao")?.ifBlank { "Almoço" } ?: "Almoço") }
    var weight by rememberSaveable { mutableStateOf((existing?.bodyWeight ?: 0.0).toString()) }
    var session by rememberSaveable { mutableStateOf(when {
        existing?.extra("fonte_questoes") == "Anki" || existing?.exercicio in catalog.decks -> "Revisão (Anki)"
        (existing?.number("tempo_video") ?: 0.0) > 0 && (existing?.number("q_certas") ?: 0.0) + (existing?.number("q_erradas") ?: 0.0) == 0.0 -> "Vídeo aula"
        else -> "Questões"
    }) }
    var subject by rememberSaveable { mutableStateOf(existing?.exercicio ?: nextSubject(rows, catalog)) }
    var topics by rememberSaveable { mutableStateOf(existing?.extra("topico_edital").orEmpty()) }
    var correct by rememberSaveable { mutableStateOf(existing?.extra("q_certas")?.ifBlank { "0" } ?: "0") }
    var wrong by rememberSaveable { mutableStateOf(existing?.extra("q_erradas")?.ifBlank { "0" } ?: "0") }
    var video by rememberSaveable { mutableStateOf(existing?.extra("tempo_video")?.ifBlank { "0" } ?: "0") }
    var source by rememberSaveable { mutableStateOf(existing?.extra("fonte_questoes")?.ifBlank { "FGV" } ?: "FGV") }
    var error by remember { mutableStateOf<String?>(null) }
    var success by remember { mutableStateOf(false) }
    val imported = existing?.extra("origem_importacao") == "simulado_json"
    val done = { success = true; error = null }
    val fields: @Composable ColumnScope.() -> Unit = {
        Field("Data (AAAA-MM-DD)", date) { date = it; success = false }
        Field("Horário (HH:MM:SS)", time) { time = it; success = false }
        if (imported) Text("Registro de simulado: a edição aqui preserva resultados, tópicos e tempos exatos. É possível ajustar data e horário.")
        else when(type) {
            "Treino" -> {
                Text(suggestTraining(rows), color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (existing == null) Choice("Formato", format, listOf("Exercício isolado", "Circuito AMRAP 20 min")) { format = it }
                if (format.startsWith("Circuito")) {
                    Text("1 round = 5 barras + 10 flexões + 15 agachamentos")
                    TimerPanel(fixedSeconds = 1200)
                    Field("Rounds completos", rounds, true) { rounds = it }
                } else {
                    Choice("Exercício", exercise, catalog.exercises + listOfNotNull(existing?.exercicio)) { exercise = it }
                    val stats = trainingMeasureSnapshot(rows, exercise)
                    if (existing == null && stats != null) {
                        Panel("SEU HISTÓRICO · $exercise") {
                            fun measured(value: Double) = if (stats.unit == "km") "%.2f km".format(value)
                                else "%.1f %s".format(value, stats.unit)
                            Text("Último treino: ${measured(stats.last)} · ${stats.lastDay}")
                            Text("Recorde: ${measured(stats.record)} em um registro")
                            Text("Média do exercício: ${measured(stats.meanPerDay)} por dia treinado · ${stats.days} dias")
                            categorySnapshot(rows, catalog.group(exercise))?.let { category ->
                                if (stats.unit == "rep") Text("Categoria ${catalog.group(exercise)}: %.1f rep por dia · %d dias".format(category.meanRepsPerDay,category.days))
                            }
                            Text("Aumente o esforço apenas com boa técnica e recuperação.", color=MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                    Field("Séries / tentativas", series, true) { series = it }
                    Field("Repetições totais", reps, true) { reps = it }
                    Field("Carga (kg)", load, true) { load = it }
                    Field("Isometria (segundos)", iso, true) { iso = it }
                    Field("Descanso (segundos)", rest, true) { rest = it }
                    Field("Cardio (minutos)", duration, true) { duration = it }
                    Field("Distância (km)", distance, true) { distance = it }
                    if (exercise in listOf("Caminhada", "Corrida")) GpsDistanceTracker { km -> distance = "%.3f".format(java.util.Locale.US, km) }
                }
                Choice("Estado mental", mood, listOf("Normal", "Foco Extremo", "Motivado", "Cansado", "Estressado")) { mood = it }
            }
            "Alimentação" -> {
                Choice("Tipo de refeição", mealType, listOf("Café da manhã", "Lanche da manhã", "Almoço", "Lanche da tarde", "Jantar", "Ceia", "Outra")) { mealType = it }
                MultiChoice("Alimentos saudáveis", healthy.split(",").map { it.trim() }.filter { it.isNotBlank() }, catalog.list("ALIMENTOS_SAUDAVEIS").sorted()) { healthy = it.joinToString(", ") }
                Field("Saudáveis — inclua outros separados por vírgula", healthy) { healthy = it }
                MultiChoice("Besteiras / alimentos ocasionais", junk.split(",").map { it.trim() }.filter { it.isNotBlank() }, catalog.list("ALIMENTOS_BESTEIROL").sorted()) { junk = it.joinToString(", ") }
                Field("Outros — separados por vírgula", junk) { junk = it }
            }
            "Peso" -> Field("Peso corporal (kg)", weight, true) { weight = it }
            "Estudo" -> {
                Choice("Tipo de sessão", session, listOf("Questões", "Vídeo aula", "Revisão (Anki)")) {
                    session = it
                    subject = if (it == "Revisão (Anki)") catalog.decks.first() else nextSubject(rows, catalog)
                    topics = ""
                }
                Choice(if (session == "Revisão (Anki)") "Deck" else "Disciplina", subject,
                    (if (session == "Revisão (Anki)") catalog.decks else catalog.subjects) + listOfNotNull(existing?.exercicio)) { subject = it; topics = "" }
                if (session != "Revisão (Anki)") {
                    val choices = listOf("🎯 Simulado / Visão Geral") + catalog.topics[subject].orEmpty()
                    MultiChoice("Tópicos do edital", choices.filter { topics.contains(it) }, choices) { topics = it.joinToString(", ") }
                    if (topics.isNotBlank()) Text(topics)
                }
                if (session == "Vídeo aula") Field("Vídeo aula (minutos)", video, true) { video = it }
                else {
                    Field("Tempo líquido (minutos)", duration, true) { duration = it }
                    if (session == "Revisão (Anki)") Field("Cartões revisados", reps, true) { reps = it }
                    else {
                        Field("Questões corretas", correct, true) { correct = it }
                        Field("Questões erradas", wrong, true) { wrong = it }
                        Choice("Fonte", source, catalog.sources + listOf(source)) { source = it }
                    }
                }
            }
        }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (success) Text("Registro salvo. Você pode consultar o histórico.")
        Button(onClick = {
            try {
                LocalDate.parse(date); LocalTime.parse(time)
                fun int(s: String): Int = s.toIntOrNull()?.takeIf { it >= 0 } ?: error("Informe números inteiros não negativos.")
                fun decimal(s: String): Double = s.replace(',', '.').toDoubleOrNull()?.takeIf { it.isFinite() && it >= 0 } ?: error("Informe números não negativos válidos.")
                val old = existing?.asMutation()
                val base = old ?: TrainingMutation(date, time, "", "")
                val extras = existing?.extras?.toMutableMap() ?: mutableMapOf()
                fun put(key: String, n: Int) { extras[key] = JsonPrimitive(n) }
                if (type == "Treino" && format.startsWith("Circuito") && existing == null) {
                    val count = int(rounds)
                    require(count > 0) { "Insira pelo menos 1 round." }
                    require(count <= Int.MAX_VALUE / 15) { "Número de rounds muito alto." }
                    val data = listOf("Barra Fixa (Pronada)" to 5, "Flexão" to 10, "Agachamento" to 15).mapIndexed { index, (name, factor) ->
                        TrainingMutation(date, time, catalog.group(name), name, series = count, repeticoes = count * factor,
                            durationMinutes = if (index == 0) 20 else 0, extras = buildJsonObject { put("humor", mood); put("isometria_tentativas", 0); put("isometria_segundos", 0) })
                    }
                    batch(data, done)
                } else {
                    val value = if (imported) base.copy(data = date, horario = time) else when(type) {
                        "Alimentação" -> {
                            require(healthy.isNotBlank() || junk.isNotBlank()) { "Selecione ao menos um alimento." }
                            extras["tipo_refeicao"] = JsonPrimitive(mealType)
                            base.copy(data = date, horario = time, group = "Nutrição", exercicio = "Refeição Diária", healthyFood = healthy, junkFood = junk, extras=JsonObject(extras))
                        }
                        "Peso" -> {
                            val kg = decimal(weight)
                            require(kg in 1.0..500.0) { "Informe um peso entre 1 e 500 kg." }
                            base.copy(data = date, horario = time, group = "Métricas", exercicio = "Peso Diário", bodyWeight = kg)
                        }
                        "Estudo" -> {
                            val anki = session == "Revisão (Anki)"
                            val isVideo = session == "Vídeo aula"
                            val c = if (anki || isVideo) 0 else int(correct)
                            val e = if (anki || isVideo) 0 else int(wrong)
                            val total = Math.addExact(c, e)
                            put("q_certas", c); put("q_erradas", e); put("tempo_video", if (isVideo) int(video) else 0)
                            extras["topico_edital"] = JsonPrimitive(if (anki) "Revisão Espaçada" else topics.ifBlank { "Geral" })
                            extras["fonte_questoes"] = JsonPrimitive(if (anki) "Anki" else if (isVideo) "Não Aplicável" else source)
                            base.copy(data = date, horario = time, group = "Estudos", exercicio = subject, repeticoes = if (anki) int(reps) else total,
                                durationMinutes = if (isVideo) 0 else int(duration), extras = JsonObject(extras))
                        }
                        else -> {
                            put("isometria_segundos", int(iso)); put("isometria_tentativas", int(series)); extras["humor"] = JsonPrimitive(mood)
                            base.copy(data = date, horario = time, group = catalog.group(exercise), exercicio = exercise, series = int(series),
                                repeticoes = int(reps), loadKg = decimal(load), restSeconds = int(rest), durationMinutes = int(duration), distanceKm = decimal(distance), extras = JsonObject(extras))
                        }
                    }
                    save(existing?.id, value, done)
                }
            } catch (e: Exception) { error = e.message ?: "Confira os campos antes de salvar." }
        }, enabled = !busy, modifier = Modifier.fillMaxWidth()) { Text(if (busy) "Salvando…" else "Salvar registro") }
    }
    if (embedded) Column(verticalArrangement = Arrangement.spacedBy(12.dp), content = fields) else Page(if (existing == null) "Registrar $type" else "Editar $type", fields)
}
