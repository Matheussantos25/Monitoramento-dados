package com.matheussantos.solem.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.semantics.*
import com.matheussantos.solem.R
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.domain.*
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable fun CharacterSheet(rows: List<TrainingRecord>) {
    val p = calculateProgress(rows)
    val weight = latestWeight(rows)
    Surface(color=MaterialTheme.colorScheme.surfaceContainer, shape=MaterialTheme.shapes.large) {
        Column(Modifier.fillMaxWidth().padding(20.dp), verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically) {
                Image(painterResource(R.drawable.character), "Personagem masculino 2D: explorador Solem", Modifier.width(110.dp).height(160.dp))
                Column(Modifier.weight(1f), verticalArrangement=Arrangement.spacedBy(8.dp)) {
                    Text("Sua ficha",style=MaterialTheme.typography.labelLarge)
                    Text("Nível ${p.xp/250+1}",style=MaterialTheme.typography.headlineMedium)
                    Text("Homem · 1,70 m")
                    Text(weight?.let { "%.1f kg\nRegistro: %s".format(it.bodyWeight,it.data.take(10)) } ?: "Peso não registrado",style=MaterialTheme.typography.bodySmall)
                }
            }
            Text("Mente · ${p.studyDays} dias de estudo     Corpo · ${p.workoutDays} dias de treino")
            Goal("Experiência",(p.xp%250).toDouble(),250)
            Text("${p.xp} XP · ${p.streak} dias seguidos · ${p.days} dias ativos")
            Text("Avatar ilustrativo. Seu peso não altera XP. Descansar faz parte da jornada.",style=MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable fun MonthlyJournal(rows: List<TrainingRecord>) {
    var monthText by rememberSaveable { mutableStateOf(YearMonth.from(today()).toString()) }
    val month = YearMonth.parse(monthText)
    val days = remember(rows,monthText) { monthlyJournal(rows,month) }
    Page("Diário de consistência") {
        Text("Um mês de cada vez. Veja os dias em que você estudou e treinou.")
        Row(verticalAlignment=Alignment.CenterVertically) {
            TextButton({ monthText=month.minusMonths(1).toString() },enabled=month.year>1900) { Text("Anterior") }
            Text(month.format(DateTimeFormatter.ofPattern("MMMM yyyy",Locale.forLanguageTag("pt-BR"))),Modifier.weight(1f),style=MaterialTheme.typography.titleMedium)
            TextButton({ monthText=month.plusMonths(1).toString() },enabled=month.year<2200) { Text("Próximo") }
        }
        TextButton({monthText=YearMonth.from(today()).toString()}) {Text("Voltar a este mês")}
        Text("${days.count { it.study }} dias de estudo · ${days.count { it.workout }} dias de treino",style=MaterialTheme.typography.titleMedium)
        Text("%.1f horas estudadas".format(days.sumOf { it.studyMinutes }/60))
        Row { listOf("S","T","Q","Q","S","S","D").forEach { Text(it,Modifier.weight(1f),textAlign=androidx.compose.ui.text.style.TextAlign.Center) } }
        val offset = month.atDay(1).dayOfWeek.value-1
        val count = ((offset+days.size+6)/7)*7
        (0 until count).chunked(7).forEach { week ->
            Row(horizontalArrangement=Arrangement.spacedBy(4.dp)) {
                week.forEach { index ->
                    val day = days.getOrNull(index-offset)
                    if (day == null) Spacer(Modifier.weight(1f).height( sixtyCell ))
                    else Surface(modifier=Modifier.weight(1f).height(sixtyCell).semantics {
                        contentDescription="${day.date}; ${if(day.study) "estudou" else "sem estudo"}; ${if(day.workout) "treinou" else "sem treino"}"
                    },color=if(day.study||day.workout) MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.surfaceContainer,
                        shape=MaterialTheme.shapes.small,border=if(day.date==today()) androidx.compose.foundation.BorderStroke(1.dp,MaterialTheme.colorScheme.primary) else null) {
                        Column(Modifier.padding(5.dp),horizontalAlignment=Alignment.CenterHorizontally) {
                            Text(day.date.dayOfMonth.toString(),style=MaterialTheme.typography.bodyMedium)
                            Text((if(day.study) "E" else "")+(if(day.workout) " T" else ""),style=MaterialTheme.typography.labelSmall)
                        }
                    }
                }
            }
        }
        Text("E = estudou · T = treinou.",style=MaterialTheme.typography.bodySmall)
        Text("Inclui Anki e vídeo-aulas. Não estimamos duração a partir de repetições. Registros futuros e sessões vazias não contam como prática.",style=MaterialTheme.typography.bodySmall)
    }
}
private val sixtyCell = 60.dp
