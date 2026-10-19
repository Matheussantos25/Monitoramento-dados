package com.matheussantos.solem.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.ui.theme.LocalDashboardPreferences
import kotlinx.serialization.json.Json
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable private fun rememberWeeklyDefinition(): WeeklyPlanDefinition {
    val context = LocalContext.current
    return remember { Json.decodeFromString<WeeklyPlanDefinition>(context.assets.open("weekly_training_plan.json").bufferedReader().use {it.readText()}) }
}

@Composable fun WorkoutProgressBars(rows: List<TrainingRecord>, generic: Boolean, available: Boolean,
    day: LocalDate = today()) {
    val definition = rememberWeeklyDefinition()
    val plan = weeklyPlanDay(rows, day, definition, !generic)
    val base = if(available) baseWorkoutPercent(rows, day, LocalDashboardPreferences.current, generic) else null
    val extra = if(available) plan.percent else null
    Panel("Treino · duas frentes") {
        Text("Treino base · ${base?.let {"$it%"} ?: "—"}",style=MaterialTheme.typography.titleMedium)
        LinearProgressIndicator(progress={(base ?: 0)/100f},modifier=Modifier.fillMaxWidth(),drawStopIndicator={})
        Text("Plano complementar · ${if(!available) "Aguardando dados" else if(plan.recovery) "Recuperação" else extra?.let {"$it%"} ?: "Sem plano"}",style=MaterialTheme.typography.titleMedium)
        if(extra != null) LinearProgressIndicator(progress={extra/100f},modifier=Modifier.fillMaxWidth(),drawStopIndicator={})
        Text("Metas base preservadas. Os percentuais são separados; excesso de um exercício não compensa outro.",style=MaterialTheme.typography.bodySmall)
    }
}

@Composable fun WorkoutPlanPage(rows: List<TrainingRecord>, generic: Boolean, available: Boolean,
    register: (String) -> Unit) {
    val definition = rememberWeeklyDefinition()
    val settings = LocalDashboardPreferences.current
    var monthText by rememberSaveable {mutableStateOf(YearMonth.from(today()).toString())}
    var selectedText by rememberSaveable {mutableStateOf(today().toString())}
    var showWeek by rememberSaveable {mutableStateOf(false)}
    val day = LocalDate.parse(selectedText)
    val month = YearMonth.parse(monthText)
    val plan = weeklyPlanDay(rows, day, definition, !generic)
    val future = day > today()
    Page("Plano e calendário de treino") {
        Text("Core e costas, sem aumentar as metas fixas. Sugestão conservadora; o histórico não mede sua capacidade máxima.")
        if(!available) Text("Aguardando o histórico. Não mostramos zero como se fosse seu resultado.")
        TextButton({selectedText=today().toString();monthText=YearMonth.from(today()).toString()}) {Text("Voltar para hoje")}
        Text(day.format(DateTimeFormatter.ofPattern("EEEE, dd/MM/yyyy",Locale.forLanguageTag("pt-BR"))),style=MaterialTheme.typography.titleLarge)
        if(!future) WorkoutProgressBars(rows,generic,available,day)
        if(!generic) {
            Text(plan.title,style=MaterialTheme.typography.titleLarge)
            Text(plan.duration + " extras · não duas horas obrigatórias")
            if(plan.recovery) Text("Sem volume extra hoje. Recuperação não é falha nem vira 100% automaticamente. Ajuste também as metas base se estiver cansado.")
            if(!plan.active) Text("O plano começa em ${definition.startsOn}. Não aplicamos metas extras retroativas.")
            plan.goals.forEach { goal ->
                Panel(goal.spec.exercise) {
                    Text("${if(available && !future) formatOneDecimal(goal.value) else "—"} / ${goal.target} ${goal.spec.unit}", style=MaterialTheme.typography.headlineSmall)
                    if(available && !future) LinearProgressIndicator(progress={goal.fraction.toFloat()},modifier=Modifier.fillMaxWidth(),drawStopIndicator={})
                    Text("${goal.spec.sets} séries de ${goal.target/goal.spec.sets} ${goal.spec.unit} · descanso ${goal.spec.restSeconds} s")
                    Text(if(goal.historyDays >= 2) "Base: ${goal.historyDays} dias nas 4 semanas anteriores." else "Pouco histórico recente dessa medida: ponto de partida conservador.",style=MaterialTheme.typography.bodySmall)
                    if(day == today()) Button({register(goal.spec.exercise)},enabled=available) {Text("Registrar exercício")}
                }
            }
            TextButton({showWeek=!showWeek}) {Text(if(showWeek) "Ocultar semana" else "Ver plano de segunda a domingo")}
            if(showWeek) {
                val monday = day.minusDays((day.dayOfWeek.value-1).toLong())
                repeat(7) {index ->
                    val date = monday.plusDays(index.toLong())
                    val item = weeklyPlanDay(rows,date,definition)
                    Text(date.format(DateTimeFormatter.ofPattern("EEEE",Locale.forLanguageTag("pt-BR"))) + " · " + item.title,style=MaterialTheme.typography.titleMedium)
                    Text(item.goals.joinToString(" · ") {"${it.spec.exercise}: ${it.target} ${it.spec.unit}"}.ifBlank {"Sem volume extra"})
                }
                Text("Metas: 70% da mediana diária das 4 semanas anteriores à segunda-feira, com limites conservadores. Regra de organização do app, não fórmula clínica validada nem prescrição da ACSM. Não mudam com os registros da própria semana.",style=MaterialTheme.typography.bodySmall)
                Text("Deixe cerca de 2–3 repetições possíveis; não busque falha técnica. Interrompa com dor, tontura ou falta de ar incomum. Sem barra disponível, não improvise suporte. A recuperação vale também para as metas base.",style=MaterialTheme.typography.bodySmall)
                Text("Treinar abdômen não remove gordura localizada nem garante definição em prazo. Sono, alimentação e recuperação importam. Referência: ACSM 2026.",style=MaterialTheme.typography.bodySmall)
            }
        }
        HorizontalDivider()
        Text("Calendário · somente treinos",style=MaterialTheme.typography.titleLarge)
        Text("B = base · P = plano. Base usa suas metas atuais. Editar o histórico recalcula o resultado. Toque em um dia.",style=MaterialTheme.typography.bodySmall)
        Row(verticalAlignment=Alignment.CenterVertically) {
            TextButton({monthText=month.minusMonths(1).toString()},enabled=month.year>1900) {Text("Anterior")}
            Text(month.format(DateTimeFormatter.ofPattern("MMM yyyy",Locale.forLanguageTag("pt-BR"))),Modifier.weight(1f))
            TextButton({monthText=month.plusMonths(1).toString()},enabled=month.year<2200) {Text("Próximo")}
        }
        Row {listOf("S","T","Q","Q","S","S","D").forEach {Text(it,Modifier.weight(1f),textAlign=androidx.compose.ui.text.style.TextAlign.Center)}}
        val offset = month.atDay(1).dayOfWeek.value-1
        val cells = ((offset+month.lengthOfMonth()+6)/7)*7
        (0 until cells).chunked(7).forEach {week ->
            Row(horizontalArrangement=Arrangement.spacedBy(3.dp)) {
                week.forEach {index ->
                    val n = index-offset+1
                    if(n !in 1..month.lengthOfMonth()) Spacer(Modifier.weight(1f).height(88.dp))
                    else {
                        val date = month.atDay(n)
                        val extra = weeklyPlanDay(rows,date,definition,!generic)
                        val known = available && date <= today()
                        val b = if(known) baseWorkoutPercent(rows,date,settings,generic) else null
                        val p = if(known) extra.percent else null
                        val recovery = known && extra.recovery
                        Surface(onClick={selectedText=date.toString()},modifier=Modifier.weight(1f).heightIn(min=88.dp).semantics {
                            contentDescription="$date, base ${b ?: "indisponível"}, plano ${p ?: if(recovery) "recuperação" else "indisponível"}"
                        },shape=MaterialTheme.shapes.small,color=if(date==day) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceContainer,
                            border=if(date==today()) BorderStroke(1.dp,MaterialTheme.colorScheme.primary) else null) {
                            Column(Modifier.padding(horizontal=3.dp,vertical=8.dp),verticalArrangement=Arrangement.spacedBy(5.dp),horizontalAlignment=Alignment.CenterHorizontally) {
                                Text("$n",style=MaterialTheme.typography.labelLarge)
                                Text("B ${b?.let {"$it%"} ?: "—"}",style=MaterialTheme.typography.labelSmall)
                                Text(if(recovery) "Recup." else "P ${p?.let {"$it%"} ?: "—"}",style=MaterialTheme.typography.labelSmall)
                            }
                        }
                    }
                }
            }
        }
        Text("Exercícios de ${day.format(DateTimeFormatter.ofPattern("dd/MM"))}",style=MaterialTheme.typography.titleLarge)
        val workouts = if(!available || future) emptyList() else rows.distinctBy {it.id}.filter {it.isWorkout() && it.data.take(10)==day.toString()}.sortedBy {it.horario}
        if(workouts.isEmpty()) Text(if(!available) "Histórico indisponível." else if(future) "Dia futuro, sem resultado ainda." else "Nenhum exercício registrado neste dia.")
        workouts.forEach { row ->
            val facts = listOfNotNull(
                "${row.repeticoes} rep".takeIf {row.repeticoes>0},
                "${formatOneDecimal(row.number("isometria_segundos"))} seg".takeIf {row.number("isometria_segundos")>0},
                "${row.durationMinutes} min".takeIf {row.durationMinutes>0},
                "${formatOneDecimal(row.distanceKm)} km".takeIf {row.distanceKm>0})
            ListItem(headlineContent={Text(row.exercicio)},supportingContent={Text("${row.horario.take(5)} · ${facts.joinToString(" · ")}")})
        }
    }
}
