package com.matheussantos.solem.ui

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.automirrored.outlined.DirectionsWalk
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.*
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.ui.theme.LocalDashboardPreferences
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable fun JourneyRing(fraction: Float, label: String, caption: String, modifier: Modifier = Modifier) {
    val settings = LocalDashboardPreferences.current
    val progress by animateFloatAsState(fraction.coerceIn(0f, 1f), tween(if(settings.motion) 650 else 0), label="Progresso")
    val primary = MaterialTheme.colorScheme.primary
    val track = MaterialTheme.colorScheme.outlineVariant
    Box(modifier.size(104.dp).semantics { contentDescription="$caption: $label" }, contentAlignment=Alignment.Center) {
        Canvas(Modifier.fillMaxSize().padding(6.dp)) {
            drawArc(track, -90f, 360f, false, style=Stroke(7.dp.toPx(), cap=StrokeCap.Round))
            drawArc(primary, -90f, 360f*progress, false, style=Stroke(7.dp.toPx(), cap=StrokeCap.Round))
        }
        Column(horizontalAlignment=Alignment.CenterHorizontally) {
            Text(label, style=MaterialTheme.typography.headlineMedium, fontFamily=FontFamily.Monospace)
            Text(caption, style=MaterialTheme.typography.labelSmall, color=MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

private fun missionIcon(id: String): ImageVector = when(id) {
    "water" -> Icons.Outlined.WaterDrop
    "sleep" -> Icons.Outlined.Bedtime
    "questions", "study" -> Icons.AutoMirrored.Outlined.MenuBook
    "walk" -> Icons.AutoMirrored.Outlined.DirectionsWalk
    else -> Icons.Outlined.FitnessCenter
}

@Composable fun JourneyDashboard(rows: List<TrainingRecord>, health: List<HealthEntry>, healthAvailable: Boolean,
    activityAvailable: Boolean, generic: Boolean, navigate: (Int) -> Unit,
    registerExercise: (String) -> Unit, healthSection: (Int) -> Unit, openWorkoutPlan: () -> Unit = {}) {
    val settings = LocalDashboardPreferences.current
    val day = today()
    val p = calculateProgress(rows)
    val definition = rememberWeeklyDefinition()
    val missions = dailyMissions(rows, health, settings, generic, healthAvailable, definition=definition).map {
        if(!activityAvailable && it.destination != 3) it.copy(value=null) else it
    }
    val done = missions.count { it.complete }
    val coverage = if(missions.isEmpty()) 0f else missions.sumOf { it.fraction.toDouble() }.toFloat()/missions.size
    val todayProgress = calculateProgress(rows.filter { it.data.take(10) == day.toString() })
    val rank = calculateRanks(rows, emptyMap(), day)
    Page(if(settings.nickname.isBlank()) "Progresso geral" else "Sua jornada, ${settings.nickname}") {
        Row(Modifier.fillMaxWidth(), verticalAlignment=Alignment.CenterVertically) {
            Text(day.format(DateTimeFormatter.ofPattern("EEEE, d 'de' MMMM",Locale.forLanguageTag("pt-BR"))),
                Modifier.weight(1f), style=MaterialTheme.typography.bodyMedium, color=MaterialTheme.colorScheme.onSurfaceVariant)
            IconButton({navigate(17)}) { Icon(Icons.Outlined.Tune,"Personalizar painel") }
        }
        Surface(shape=MaterialTheme.shapes.extraLarge, color=MaterialTheme.colorScheme.surfaceContainer) {
          Column(Modifier.padding(20.dp),verticalArrangement=Arrangement.spacedBy(18.dp)) {
            Text("MISSÕES / HOJE",style=MaterialTheme.typography.labelSmall,color=MaterialTheme.colorScheme.primary)
            Row(Modifier.fillMaxWidth(), horizontalArrangement=Arrangement.spacedBy(14.dp), verticalAlignment=Alignment.CenterVertically) {
                JourneyRing(coverage, "${(coverage*100).toInt()}%", "do dia")
                Column(Modifier.weight(1f), verticalArrangement=Arrangement.spacedBy(7.dp)) {
                    Text(if(missions.isNotEmpty() && done==missions.size) "Dia conquistado." else "Uma missão\nde cada vez.",style=MaterialTheme.typography.headlineMedium)
                    Text("$done / ${missions.size} concluídas",color=MaterialTheme.colorScheme.primary,style=MaterialTheme.typography.labelLarge)
                    if(missions.any {it.value==null}) Text("Progresso parcial · aguardando dados",style=MaterialTheme.typography.bodySmall)
                }
            }
            HorizontalDivider(color=MaterialTheme.colorScheme.outlineVariant)
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
                Text(if(activityAvailable) "NÍVEL ${p.xp/250+1}" else "NÍVEL —",style=MaterialTheme.typography.labelLarge)
                Text(if(activityAvailable) "${p.xp%250} / 250 XP" else "Sincronizando",style=MaterialTheme.typography.labelLarge,color=MaterialTheme.colorScheme.primary)
            }
            LinearProgressIndicator(progress={if(activityAvailable) (p.xp%250)/250f else 0f},modifier=Modifier.fillMaxWidth(),drawStopIndicator={})
            Text(if(activityAvailable) "${p.streak} dias de sequência · +${todayProgress.xp} XP hoje" else "Seu histórico aparece ao sincronizar.",
                 style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
          }
        }
        WorkoutProgressBars(rows,generic,activityAvailable)
        CycleTodayCards(rows,generic,activityAvailable,registerExercise,openWorkoutPlan)
        Button(openWorkoutPlan,modifier=Modifier.fillMaxWidth()) {Text("Plano semanal e calendário de treino")}
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            QuickDestination("Treinar", Icons.Outlined.FitnessCenter, Modifier.weight(1f)) { navigate(1) }
            QuickDestination("Água", Icons.Outlined.WaterDrop, Modifier.weight(1f)) { healthSection(1) }
            if(!generic) QuickDestination("Estudar", Icons.AutoMirrored.Outlined.MenuBook, Modifier.weight(1f)) { navigate(5) }
            QuickDestination("Refeição", Icons.Outlined.Restaurant, Modifier.weight(1f)) { healthSection(0) }
        }
        Surface(onClick={navigate(10)}, shape=MaterialTheme.shapes.large, color=MaterialTheme.colorScheme.primaryContainer) {
            Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                RankEmblem(rank.tier, Modifier.size(92.dp,72.dp))
                Column(Modifier.weight(1f), verticalArrangement=Arrangement.spacedBy(5.dp)) {
                    Text(if(activityAvailable) "Elo físico · ${rankNames[rank.tier]}" else "Seu elo físico",style=MaterialTheme.typography.titleMedium)
                    Text(if(activityAvailable) "${rank.reps} repetições no histórico" else "Aguardando histórico",style=MaterialTheme.typography.bodySmall)
                    Text(if(generic) "Ver evolução física" else "Ver físico e estudos", style=MaterialTheme.typography.labelLarge, color=MaterialTheme.colorScheme.primary)
                }
                Icon(Icons.Outlined.ChevronRight, "Abrir elos")
            }
        }
        Row(Modifier.fillMaxWidth(), verticalAlignment=Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("Missões de hoje", style=MaterialTheme.typography.titleLarge)
                Text("$done de ${missions.size} concluídas", color=MaterialTheme.colorScheme.onSurfaceVariant)
            }
            IconButton({navigate(17)}) {Icon(Icons.Outlined.Tune,"Ajustar metas")}
        }
        if(missions.isEmpty()) Text("Suas missões estão ocultas. Ative as que combinam com sua rotina em Personalizar.")
        missions.forEach { mission ->
            MissionTile(mission) {
                when {
                    mission.id == "water" -> healthSection(1)
                    mission.id == "sleep" -> healthSection(3)
                    mission.exercise != null -> registerExercise(mission.exercise)
                    else -> navigate(mission.destination)
                }
            }
        }
        Text("Metas pessoais, não prescrições de saúde. Elas não mudam as regras de XP ou dos elos.",
            style=MaterialTheme.typography.bodySmall, color=MaterialTheme.colorScheme.onSurfaceVariant)
        Text(if(generic) "XP por constância: +30 por dia de treino. Descansar não apaga sua evolução." else "XP por constância: treino +30 · estudo +30 · ambos +15. Descansar não apaga sua evolução.",
            style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
        if(settings.showWeek) {
            Text("Seu ritmo nesta semana",style=MaterialTheme.typography.titleLarge)
            WeekRhythm(rows)
            TextButton({navigate(9)}) { Icon(Icons.Outlined.CalendarMonth,null); Spacer(Modifier.width(8.dp)); Text("Abrir calendário mensal") }
        }
        if(settings.showRecent) {
            Text("Últimas sessões", style=MaterialTheme.typography.titleLarge)
            if(rows.isEmpty()) Text(if(activityAvailable) "Seu primeiro registro inicia a jornada. Use um dos atalhos acima." else "Seu histórico ainda não está disponível.")
            rows.sortedWith(compareByDescending<TrainingRecord> { it.data }.thenByDescending { it.horario }).take(3).forEach { row ->
                ListItem(headlineContent={Text(row.exercicio)}, supportingContent={Text("${row.data.take(10)} · ${row.horario.take(5)}")},
                    leadingContent={Icon(if(row.isWorkout()) Icons.Outlined.FitnessCenter else Icons.AutoMirrored.Outlined.MenuBook,null)},
                    colors=ListItemDefaults.colors(containerColor=MaterialTheme.colorScheme.background))
            }
        }
    }
}

@Composable private fun QuickDestination(title: String, icon: ImageVector, modifier: Modifier, onClick: () -> Unit) {
    Surface(onClick=onClick,modifier=modifier.heightIn(min=84.dp),shape=MaterialTheme.shapes.medium,color=MaterialTheme.colorScheme.surfaceContainer) {
        Column(Modifier.padding(vertical=14.dp,horizontal=4.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(8.dp)) {
            Icon(icon,null,tint=MaterialTheme.colorScheme.primary)
            Text(title,style=MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable private fun MissionTile(mission: DailyMission, onClick: () -> Unit) {
    val progress by animateFloatAsState(mission.fraction, tween(if(LocalDashboardPreferences.current.motion) 450 else 0),label="Missão")
    Surface(onClick=onClick,shape=MaterialTheme.shapes.large,color=MaterialTheme.colorScheme.surfaceContainer) {
        Column(Modifier.fillMaxWidth().padding(16.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                Box(Modifier.size(44.dp).background(MaterialTheme.colorScheme.primaryContainer,MaterialTheme.shapes.small),contentAlignment=Alignment.Center) {
                    Icon(missionIcon(mission.id),null,tint=MaterialTheme.colorScheme.primary)
                }
                Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(3.dp)) {
                    Text(mission.title,style=MaterialTheme.typography.titleMedium)
                    Row(verticalAlignment=Alignment.Bottom,horizontalArrangement=Arrangement.spacedBy(5.dp)) {
                        Text(mission.value?.let {formatOneDecimal(it)} ?: "—",
                             style=MaterialTheme.typography.headlineMedium,fontFamily=FontFamily.Monospace)
                        Text("/ ${mission.target} ${mission.unit}",style=MaterialTheme.typography.bodySmall,
                             color=MaterialTheme.colorScheme.onSurfaceVariant,modifier=Modifier.padding(bottom=4.dp))
                    }
                }
                Icon(if(mission.complete) Icons.Outlined.CheckCircle else Icons.Outlined.AddCircleOutline,
                    if(mission.complete) "Meta concluída. Abrir registros" else "Registrar atividade",tint=MaterialTheme.colorScheme.primary)
            }
            LinearProgressIndicator(progress={progress},modifier=Modifier.fillMaxWidth().height(5.dp),drawStopIndicator={})
            Text(when {mission.value==null -> "Aguardando sincronização";mission.complete -> "Concluída · ver registros";else -> "Registrar · continuar missão"},
                 style=MaterialTheme.typography.labelSmall,color=MaterialTheme.colorScheme.primary)
        }
    }
}

@Composable private fun WeekRhythm(rows: List<TrainingRecord>) {
    val day = today()
    val start = day.minusDays((day.dayOfWeek.value-1).toLong())
    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(6.dp)) {
        listOf("S","T","Q","Q","S","S","D").forEachIndexed { index,label ->
            val date = start.plusDays(index.toLong())
            val active = date <= day && calculateProgress(rows.filter { it.data.take(10)==date.toString() },date).days > 0
            Column(Modifier.weight(1f),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(9.dp)) {
                Text(label,style=MaterialTheme.typography.labelSmall)
                Box(Modifier.size(36.dp).background(if(active) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceContainer,CircleShape)
                    .then(if(date==day) Modifier.border(1.dp,MaterialTheme.colorScheme.primary,CircleShape) else Modifier)
                    .semantics { contentDescription="$date: ${if(active) "atividade registrada" else "sem atividade registrada"}" },contentAlignment=Alignment.Center) {
                    if(active) Icon(Icons.Outlined.Check,null,Modifier.size(18.dp),tint=MaterialTheme.colorScheme.primary)
                    else Text("${date.dayOfMonth}",style=MaterialTheme.typography.labelSmall)
                }
            }
        }
    }
}
