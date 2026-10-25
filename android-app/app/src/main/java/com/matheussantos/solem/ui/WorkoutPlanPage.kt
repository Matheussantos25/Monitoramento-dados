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

@Composable internal fun rememberWeeklyDefinition(): WeeklyPlanDefinition {
    val context = LocalContext.current
    return remember { Json.decodeFromString<WeeklyPlanDefinition>(context.assets.open("weekly_training_plan.json").bufferedReader().use {it.readText()}) }
}

@Composable fun WorkoutProgressBars(rows: List<TrainingRecord>, generic: Boolean, available: Boolean,
    day: LocalDate = today()) {
    val definition = rememberWeeklyDefinition()
    val plan = weeklyPlanDay(rows, day, definition, !generic)
    val base = if(available) baseWorkoutPercent(rows, day, LocalDashboardPreferences.current, generic, definition) else null
    val extra = if(available) plan.percent else null
    Panel(if(plan.cycle) "Ciclo de 4 semanas" else "Treino · duas frentes") {
        Text("Treino base · ${base?.let {"$it%"} ?: "—"}",style=MaterialTheme.typography.titleMedium)
        LinearProgressIndicator(progress={(base ?: 0)/100f},modifier=Modifier.fillMaxWidth(),drawStopIndicator={})
        Text("${if(plan.cycle) "Sessão completa" else "Plano complementar"} · ${if(!available) "Aguardando dados" else if(plan.recovery) "Recuperação" else extra?.let {"$it%"} ?: "Sem plano"}",style=MaterialTheme.typography.titleMedium)
        if(extra != null) LinearProgressIndicator(progress={extra/100f},modifier=Modifier.fillMaxWidth(),drawStopIndicator={})
        Text(if(plan.cycle) "A base está incluída na sessão completa. Não some as metas antigas. Histórico e preferências preservados." else "Metas base preservadas. Os percentuais são separados; excesso de um exercício não compensa outro.",style=MaterialTheme.typography.bodySmall)
    }
}

@Composable fun WorkoutPlanPage(rows: List<TrainingRecord>, generic: Boolean, available: Boolean,
    register: (String) -> Unit) {
    val definition = rememberWeeklyDefinition()
    val settings = LocalDashboardPreferences.current
    var monthText by rememberSaveable {mutableStateOf(YearMonth.from(today()).toString())}
    var selectedText by rememberSaveable {mutableStateOf(today().toString())}
    var showWeek by rememberSaveable {mutableStateOf(false)}
    var previewWeek by rememberSaveable {mutableStateOf(0)}
    var showCycle by rememberSaveable {mutableStateOf(false)}
    val day = LocalDate.parse(selectedText)
    val month = YearMonth.parse(monthText)
    val plan = weeklyPlanDay(rows, day, definition, !generic)
    val future = day > today()
    Page("Plano e calendário de treino") {
        Text("Força de corpo inteiro às segundas, quartas e sextas; caminhada às terças e quintas; recuperação no fim de semana. O histórico não mede capacidade máxima.")
        if(!generic) (definition.cycleRevised ?: definition.cycle)?.let {cycle ->
            val start = LocalDate.parse(cycle.startsOn)
            Text("Ciclo revisado: 26/10 a 22/11/2026 · a base já está incluída na sessão. Datas anteriores preservam o plano original.")
            if(day < start) Button({selectedText=start.toString();monthText=YearMonth.from(start).toString()}) {Text("Ver início do novo ciclo")}
            if(plan.cycleWeek > 0) Text("Semana ${plan.cycleWeek}/4 · ${plan.phase}",style=MaterialTheme.typography.titleMedium)
            if(plan.held) Text("Etapa mantida: faltaram registros suficientes de conclusão na semana anterior. Não tente compensar sessões perdidas.")
            Text("Semanas 1–3: progressão gradual. Semana 4: menos volume para recuperar. O app só avança com pelo menos 2 sessões de força a 80% de cada exercício na semana anterior. Isso mede registro, não recuperação: reduza ou descanse se houver fadiga ou perda de técnica.",style=MaterialTheme.typography.bodySmall)
            TextButton({showCycle=!showCycle}) {Text(if(showCycle) "Ocultar ciclo" else "Ver as 4 semanas · progressão planejada")}
            if(showCycle) {
                Row(horizontalArrangement=Arrangement.spacedBy(6.dp)) {
                    repeat(4) {n -> FilterChip(selected=previewWeek==n,onClick={previewWeek=n},label={Text("${n+1}")})}
                }
                Text(cycle.labels[previewWeek],style=MaterialTheme.typography.titleMedium)
                Text("Prévia se houver progressão. Faça 5–10 minutos de aquecimento leve e séries fáceis antes da força.",style=MaterialTheme.typography.bodySmall)
                repeat(7) {offset ->
                    val date=start.plusDays(previewWeek*7L+offset)
                    val item=trainingCycleDay(rows,date,cycle,previewStage=previewWeek)
                    Text(date.format(DateTimeFormatter.ofPattern("dd/MM"))+" · "+item.title,style=MaterialTheme.typography.titleSmall)
                    Text(item.goals.joinToString(" · ") {"${it.spec.exercise}: ${it.spec.sets}×${it.target/it.spec.sets} ${it.spec.unit}"}.ifBlank {"Sem meta obrigatória"},style=MaterialTheme.typography.bodySmall)
                }
            }
        }
        if(!available) Text("Aguardando o histórico. Não mostramos zero como se fosse seu resultado.")
        TextButton({selectedText=today().toString();monthText=YearMonth.from(today()).toString()}) {Text("Voltar para hoje")}
        Text(day.format(DateTimeFormatter.ofPattern("EEEE, dd/MM/yyyy",Locale.forLanguageTag("pt-BR"))),style=MaterialTheme.typography.titleLarge)
        if(!future) WorkoutProgressBars(rows,generic,available,day)
        if(!generic) {
            Text(plan.title,style=MaterialTheme.typography.titleLarge)
            Text(plan.duration + if(plan.cycle) " · sessão total, incluindo a base" else " extras")
            if(plan.recovery) Text("Recuperação: sem treino obrigatório do ciclo hoje. Não é falha nem vira 100% automaticamente.")
            if(!plan.active) Text(if(plan.completed) "Ciclo encerrado. Revise a recuperação e os resultados antes de iniciar outro; as metas antigas não voltam automaticamente." else "O plano começa em ${definition.startsOn}. Não aplicamos metas extras retroativas.")
            plan.goals.forEach { goal ->
                CycleGoalCard(goal, available, future, day == today(), register)
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
                Text(if(plan.cycle) "Flexão e agachamento partem da capacidade que você relatou. Nos demais, usamos registros com 2–8 séries anteriores ao ciclo: 80% da mediana por série, com limites conservadores. Sem referência suficiente na barra, usamos remada. É uma heurística do app, não uma avaliação clínica. Registre repetições totais e a quantidade real de séries." else "Metas anteriores ao ciclo: 70% da mediana diária, com limites conservadores.",style=MaterialTheme.typography.bodySmall)
                Text("Deixe cerca de 2–3 repetições possíveis; não busque falha técnica. Interrompa com dor, tontura ou falta de ar incomum. Sem barra disponível, não improvise suporte. A recuperação vale também para as metas base.",style=MaterialTheme.typography.bodySmall)
                Text("Treinar abdômen não remove gordura localizada nem garante definição em prazo. Sono, alimentação e recuperação importam. Referência: ACSM 2026.",style=MaterialTheme.typography.bodySmall)
            }
        }
        HorizontalDivider()
        Text("Calendário · somente treinos",style=MaterialTheme.typography.titleLarge)
        Text("B = base do dia · P = sessão completa. No ciclo, B já faz parte de P. Datas anteriores mantêm a regra antiga. Editar registros recalcula o resultado. Toque em um dia.",style=MaterialTheme.typography.bodySmall)
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
                        val b = if(known) baseWorkoutPercent(rows,date,settings,generic,definition) else null
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

@Composable fun CycleGoalCard(goal: PlanGoal, available: Boolean, future: Boolean,
    canRegister: Boolean, register: (String) -> Unit) {
    var details by rememberSaveable(goal.spec.exercise) {mutableStateOf(false)}
    Surface(shape=MaterialTheme.shapes.large,color=MaterialTheme.colorScheme.surfaceContainer,
        border=BorderStroke(1.dp,MaterialTheme.colorScheme.outlineVariant)) {
        Column(Modifier.fillMaxWidth().padding(18.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
                Text(goal.spec.exercise,Modifier.weight(1f),style=MaterialTheme.typography.titleMedium)
                Text(if(future) "Programado" else if(!available) "Sincronizando" else if(goal.fraction>=1) "Concluído" else "Em andamento",
                    style=MaterialTheme.typography.labelSmall,color=MaterialTheme.colorScheme.primary)
            }
            Text("${if(available && !future) formatOneDecimal(goal.value) else "—"} / ${goal.target} ${goal.spec.unit}",style=MaterialTheme.typography.headlineMedium)
            LinearProgressIndicator(progress={if(available && !future) goal.fraction.toFloat() else 0f},modifier=Modifier.fillMaxWidth().height(6.dp),drawStopIndicator={})
            Text(if(goal.spec.unit=="km") "Distância total do dia · deslocamentos já contam" else "${goal.spec.sets} séries × ${goal.target/goal.spec.sets} ${goal.spec.unit} · descanso ${goal.spec.restSeconds} s",
                style=MaterialTheme.typography.bodyMedium)
            Button({register(goal.spec.exercise)},enabled=available && canRegister,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)) {
                Text(if(goal.fraction>=1 && !future) "Ver registro" else "Registrar exercício")
            }
            TextButton({details=!details}) { Text(if(details) "Ocultar orientação" else "Orientação da sessão") }
            if(details) Text(goal.spec.note,style=MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable fun CycleTodayCards(rows: List<TrainingRecord>, generic: Boolean, available: Boolean,
    register: (String) -> Unit, openPlan: () -> Unit) {
    if(generic) return
    val plan=weeklyPlanDay(rows,today(),rememberWeeklyDefinition())
    Text("Seu ciclo de treino",style=MaterialTheme.typography.headlineSmall)
    Text(plan.title,style=MaterialTheme.typography.titleMedium)
    if(plan.recovery) {
        Text("Hoje é recuperação. O descanso faz parte do ciclo.")
        OutlinedButton(openPlan,modifier=Modifier.fillMaxWidth()) {Text("Ver próximas sessões")}
    }
    if(plan.goals.isNotEmpty()) Text("${plan.goals.count {it.fraction>=1}} de ${plan.goals.size} exercícios concluídos · base incluída",style=MaterialTheme.typography.bodySmall)
    plan.goals.forEach { CycleGoalCard(it,available,false,true,register) }
}
