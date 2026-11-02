package com.matheussantos.solem.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.Alignment
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalContext
import androidx.compose.foundation.text.selection.SelectionContainer
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.domain.*

@Composable fun Bars(title: String, points: List<Pair<String, Double>>, unit: String = "") {
    Panel(title) { CleanBars(points,unit) }
}

@Composable fun CleanBars(points: List<Pair<String, Double>>, unit: String = "") {
    var showValues by rememberSaveable { mutableStateOf(false) }
    val accent=MaterialTheme.colorScheme.primary
    val muted=MaterialTheme.colorScheme.outlineVariant
    val maximum=(points.maxOfOrNull {it.second} ?: 0.0).coerceAtLeast(if(unit=="%")100.0 else 1.0)
    val chronological=points.all {it.first.matches(Regex("[0-9/:-]+h?"))}
    fun display(label:String)=runCatching {java.time.LocalDate.parse(label.take(10)).format(java.time.format.DateTimeFormatter.ofPattern("dd/MM"))}.getOrDefault(label)
    if(points.isEmpty()) Text("Sem dados para os filtros selecionados.")
    else if(chronological) {
        BoxWithConstraints(Modifier.fillMaxWidth()) {
            val slot=(maxWidth/points.size).coerceAtLeast(44.dp)
            Row(Modifier.horizontalScroll(rememberScrollState()),verticalAlignment=Alignment.Bottom) {
                points.forEach {(label,value) ->
                    Column(Modifier.width(slot).semantics {contentDescription="$label: ${formatOneDecimal(value)} $unit"},
                        horizontalAlignment=Alignment.CenterHorizontally) {
                        Box(Modifier.fillMaxWidth().height(178.dp),contentAlignment=Alignment.BottomCenter) {
                            Column(horizontalAlignment=Alignment.CenterHorizontally) {
                                if(value>0)Text(formatOneDecimal(value),style=MaterialTheme.typography.labelSmall)
                                Spacer(Modifier.height(7.dp))
                                if(value>0)Box(Modifier.width(28.dp).height((value/maximum*142).toFloat().dp)
                                    .clip(RoundedCornerShape(topStart=7.dp,topEnd=7.dp,bottomStart=3.dp,bottomEnd=3.dp))
                                    .background(Brush.verticalGradient(listOf(accent,accent.copy(alpha=0.3f)))))
                                else Box(Modifier.width(12.dp).height(3.dp).background(muted,RoundedCornerShape(2.dp)))
                            }
                        }
                        Spacer(Modifier.height(10.dp))
                        Text(display(label),style=MaterialTheme.typography.labelSmall)
                    }
                }
            }
        }
        Text(if(points.size>7)"$unit · Deslize para ver todo o período" else unit,style=MaterialTheme.typography.bodySmall)
    } else {
        points.forEach {(label,value) ->
            Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                    Text(label,Modifier.weight(1f),style=MaterialTheme.typography.bodySmall)
                    Text("${formatOneDecimal(value)} $unit",style=MaterialTheme.typography.labelMedium)
                }
                Box(Modifier.fillMaxWidth().height(12.dp).clip(RoundedCornerShape(5.dp)).background(muted.copy(alpha=0.25f))) {
                    if(value>0)Box(Modifier.fillMaxWidth((value/maximum).toFloat().coerceIn(0f,1f)).fillMaxHeight()
                        .clip(RoundedCornerShape(5.dp)).background(Brush.horizontalGradient(listOf(accent.copy(alpha=0.4f),accent))))
                }
                Spacer(Modifier.height(8.dp))
            }
        }
    }
    if(points.isNotEmpty()) {
        TextButton({showValues=!showValues}){Text(if(showValues)"Ocultar valores" else "Ver valores do gráfico")}
        if(showValues)points.forEach {(label,value)->Text("$label · ${formatOneDecimal(value)} $unit",style=MaterialTheme.typography.bodyMedium)}
    }
}
@Composable fun PrivateWeightLine(rows: List<HealthEntry>) {
    val points = rows.filter { it.kind == "weight" && it.number("kg") in 1.0..500.0 }
        .groupBy { it.day }.toSortedMap().map { it.key to it.value.map { r -> r.number("kg") }.average() }
    Panel("Evolução do peso corporal") {
        if (points.isEmpty()) Text("Sem registros de peso.")
        else {
            val color = MaterialTheme.colorScheme.primary
            val min = points.minOf { it.second }
            val max = points.maxOf { it.second }
            Canvas(Modifier.fillMaxWidth().height(170.dp).semantics {contentDescription="Evolução do peso. Valores disponíveis abaixo do gráfico."}) {
                val path = Path()
                points.forEachIndexed { index, (_, value) ->
                    val x = 12 + (size.width - 24) * index / (points.size - 1).coerceAtLeast(1)
                    val y = size.height - 12 - ((value - min) / (max - min).coerceAtLeast(1.0) * (size.height - 24)).toFloat()
                    if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
                    drawCircle(color, 5f, Offset(x, y))
                }
                val area=Path().apply {addPath(path);lineTo(size.width-12,size.height);lineTo(12f,size.height);close()}
                drawPath(area,Brush.verticalGradient(listOf(color.copy(alpha=0.18f),Color.Transparent)))
                drawPath(path, color, style = androidx.compose.ui.graphics.drawscope.Stroke(3f))
            }
            Text("%.1f – %.1f kg • %s a %s".format(min, max, points.first().first, points.last().first))
            var showWeights by rememberSaveable {mutableStateOf(false)}
            TextButton({showWeights=!showWeights}) {Text(if(showWeights)"Ocultar valores" else "Ver valores do gráfico")}
            if(showWeights)points.forEach {(date,weight)->Text("$date · %.1f kg".format(weight))}
        }
    }
}
@Composable fun PhysicalCharts(rows: List<TrainingRecord>, catalog: Catalog) {
    var period by rememberSaveable { mutableStateOf(catalog.periods.first()) }
    var exercises by rememberSaveable { mutableStateOf(listOf<String>()) }
    val all = filterPeriod(rows, period)
    val training = all.filter { it.isWorkout() }
    val available = (catalog.exercises + training.map { it.exercicio }).distinct().sorted()
    val selected = training.filter { exercises.isEmpty() || it.exercicio in exercises }
    fun totals(value: (TrainingRecord) -> Double) = selected.groupBy { it.data }.toSortedMap().map { it.key to it.value.sumOf(value) }.filter { it.second > 0 }
    Page("Evolução física") {
        Choice("Período", period, catalog.periods) { period = it }
        MultiChoice("Filtrar por exercício (vazio = todos)", exercises, available) { exercises = it }
        if (selected.any { it.repeticoes > 0 } || exercises.isEmpty())
            Goal("Repetições de hoje", selected.filter { it.data.take(10) == today().toString() }.sumOf { it.repeticoes.toDouble() }, 200)
        Panel("RESUMO DO FILTRO") {
            Text("${selected.map { it.data.take(10) }.distinct().size} dias treinados • ${selected.sumOf { it.repeticoes.toLong() }} repetições")
            Text("%.1f kg de carga máxima • %.2f km • %d min".format(
                selected.maxOfOrNull { it.loadKg } ?: 0.0, selected.sumOf { it.distanceKm }, selected.sumOf { it.durationMinutes }))
        }
        Bars("Repetições por dia", totals { it.repeticoes.toDouble() }, "reps")
        Bars("Distância por dia", totals { it.distanceKm }, "km")
        Bars("Cardio por dia", totals { if (it.number("isometria_segundos") > 0) 0.0 else it.durationMinutes.toDouble() }, "min")
        Bars("Isometria por dia", totals { it.number("isometria_segundos") }, "s")
    }
}
@Composable fun StudyCharts(rows: List<TrainingRecord>, catalog: Catalog) {
    val context = LocalContext.current
    var showSyllabus by rememberSaveable { mutableStateOf(false) }
    val syllabus = remember { context.assets.open("edital.txt").bufferedReader().use { it.readText() } }
    var period by rememberSaveable { mutableStateOf(catalog.periods.first()) }
    var source by rememberSaveable { mutableStateOf("Todas") }
    var discipline by rememberSaveable { mutableStateOf("Todas") }
    var from by rememberSaveable { mutableStateOf("") }
    var to by rememberSaveable { mutableStateOf("") }
    val periodRows = filterPeriod(rows, period).filter { it.group == "Estudos" }
    val study = periodRows.filter { source == "Todas" || it.extra("fonte_questoes") == source }
    val questions = study.filter { it.extra("fonte_questoes") != "Anki" }
    fun accuracy(list: List<TrainingRecord>): Double {
        val correct = list.sumOf { it.number("q_certas") }
        val total = correct + list.sumOf { it.number("q_erradas") }
        return if (total > 0) correct / total * 100 else 0.0
    }
    val topics = questions.groupBy { it.exercicio + " • " + it.extra("topico_edital").ifBlank { "Geral" } }
    Page("Evolução nos estudos") {
        if (!catalog.generic) {
            OutlinedButton({ showSyllabus = !showSyllabus }) { Text(if (showSyllabus) "Ocultar edital" else "Ver edital completo") }
            if (showSyllabus) SelectionContainer { Text(syllabus) }
        }
        Choice("Período", period, catalog.periods) { period = it }
        Goal("Questões de hoje", periodRows.filter { it.data == today().toString() && it.extra("fonte_questoes") != "Anki" }.sumOf { it.repeticoes.toDouble() }, if (catalog.generic) 10 else 150)
        Choice("Fonte", source, listOf("Todas") + periodRows.map { it.extra("fonte_questoes") }.distinct()) { source = it }
        Panel("Seu desempenho") {
            Text("%.1f horas líquidas • %.1f%% de acerto".format(study.sumOf { it.studyMinutes() } / 60, accuracy(questions)))
            Text("${questions.sumOf { it.repeticoes.toLong() }} questões • %.1f horas de Anki".format(study.filter { it.extra("fonte_questoes") == "Anki" }.sumOf { it.studyMinutes() } / 60))
            Text("%.1f horas de vídeo aula".format(study.sumOf { it.number("tempo_video") } / 60))
        }
        Bars("Tópicos que merecem atenção (mínimo 5 questões)", topics.filter { (_, r) -> r.sumOf { it.number("q_certas")+it.number("q_erradas") } >= 5 }.map { it.key to accuracy(it.value) }.sortedBy { it.second }.take(5), "%")
        Bars("Tópicos menos explorados", topics.map { it.key to it.value.sumOf { r -> r.repeticoes.toDouble() } }.sortedBy { it.second }.take(10), "questões")
        Field("Gráfico diário: início AAAA-MM-DD (opcional)", from) { from = it }
        Field("Gráfico diário: fim AAAA-MM-DD (opcional)", to) { to = it }
        val validDates = listOf(from,to).all { it.isBlank() || runCatching { java.time.LocalDate.parse(it) }.isSuccess } && (from.isBlank() || to.isBlank() || from <= to)
        if (!validDates) Text("Informe datas válidas, com o início anterior ao fim.", color = MaterialTheme.colorScheme.error)
        else Bars("Questões por dia", questions.filter { (from.isBlank() || it.data >= from) && (to.isBlank() || it.data <= to) }.groupBy { it.data }.toSortedMap().map { it.key to it.value.sumOf { r -> r.repeticoes.toDouble() } }, "questões")
        Bars("Acerto por disciplina", questions.groupBy { it.exercicio }.filter { it.value.sumOf { r -> r.number("q_certas") + r.number("q_erradas") } > 0 }.map { it.key to accuracy(it.value) }, "%")
        Choice("Análise por disciplina", discipline, listOf("Todas") + study.map { it.exercicio }.distinct()) { discipline = it }
        val granular = study.filter { discipline == "Todas" || it.exercicio == discipline }.groupBy { it.exercicio + " • " + it.extra("topico_edital").ifBlank { "Geral" } }
        Bars("Tempo por tópico", granular.map { it.key to it.value.sumOf { r -> r.studyMinutes() } / 60 }.sortedByDescending { it.second }.take(10), "h")
        Bars("Acerto por tópico", granular.filter { it.value.sumOf { r -> r.number("q_certas") + r.number("q_erradas") } > 0 }.map { it.key to accuracy(it.value) }.sortedByDescending { it.second }.take(10), "%")
        Panel("Cronograma estratégico — próximos 30 dias") {
            val indices = mutableMapOf<String, Int>()
            repeat(30) { i ->
                val subject = catalog.route[i % catalog.route.size]
                val choices = catalog.topics[subject].orEmpty().filterNot { "Simulado" in it }.ifEmpty { listOf("Revisão / Exercícios Gerais") }
                val index = indices[subject] ?: 0
                indices[subject] = index+1
                Text("${today().plusDays(i.toLong())} • $subject\n${choices[index % choices.size]}")
                HorizontalDivider()
            }
            Text(if (catalog.generic) "Sugestões de revisão; adapte seu planejamento na aba Cronograma." else "Inclua Matemática e Português diariamente.")
        }
    }
}
