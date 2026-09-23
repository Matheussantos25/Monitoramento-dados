package com.matheussantos.solem.ui

import android.media.AudioManager
import android.media.ToneGenerator
import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.domain.*
import kotlinx.coroutines.delay

@Composable fun RanksPage(rows: List<TrainingRecord>, catalog: Catalog) {
    val ranks = calculateRanks(rows, catalog.topics, today())
    var subject by rememberSaveable { mutableStateOf(catalog.topics.keys.first()) }
    var promoted by remember { mutableStateOf(false) }
    var promotedTier by remember { mutableIntStateOf(0) }
    val highWater = remember { mutableMapOf<String, Int>() }
    LaunchedEffect(ranks) {
        val current = ranks.topics.associate { "${it.subject}|${it.topic}" to it.tier } + ("physical" to ranks.tier)
        val promotions = if (highWater.isEmpty()) emptyList() else current.filter { (k, v) -> v > (highWater[k] ?: v) }.values
        current.forEach { (k, v) -> highWater[k] = maxOf(v, highWater[k] ?: v) }
        if (promotions.isNotEmpty()) {
            promotedTier = promotions.maxOrNull() ?: ranks.tier
            promoted = true
            val tone = runCatching { ToneGenerator(AudioManager.STREAM_MUSIC, 38) }.getOrNull()
            try {
                tone?.startTone(ToneGenerator.TONE_PROP_BEEP2, 180); delay(210)
                tone?.startTone(ToneGenerator.TONE_PROP_ACK, 520); delay(560)
            } finally { tone?.release() }
            delay(4000)
            promoted = false
        }
    }
    Page("Sua jornada ranqueada") {
        Text("Elos pessoais derivados do histórico. Não são avaliação de saúde nem previsão de aprovação.")
        AnimatedVisibility(
            visible = promoted,
            enter = fadeIn(tween(500)) + scaleIn(tween(700), initialScale = .72f),
            exit = fadeOut(tween(700)) + scaleOut(tween(700), targetScale = 1.08f)
        ) {
            Surface(
                color = MaterialTheme.colorScheme.surfaceContainerHigh,
                shape = RoundedCornerShape(24.dp),
                tonalElevation = 8.dp,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(4.dp),
                    modifier = Modifier.padding(vertical = 26.dp, horizontal = 18.dp)
                ) {
                    Text("PROMOÇÃO DE ELO", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelLarge)
                    RankEmblem(promotedTier)
                    Text(rankNames[promotedTier], style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Black)
                    Text("Seu histórico alcançou uma nova patente.")
                }
            }
        }
        Panel("Físico · ${rankNames[ranks.tier]}") {
            RankEmblem(ranks.tier)
            Text("${ranks.reps} repetições registradas")
            if (ranks.tier < 7) {
                val start = repLimits[ranks.tier]
                val target = repLimits[ranks.tier + 1]
                LinearProgressIndicator(progress = { (ranks.reps - start).toFloat() / (target - start) })
                Text("${rankNames[ranks.tier + 1]}: faltam ${target - ranks.reps} repetições, no seu ritmo")
            }
            Text("Sem perda por descanso. Séries não multiplicam o total. Cardio e isometria permanecem no XP e calendário.")
        }
        Choice("Disciplina do edital", subject, catalog.topics.keys.toList()) { subject = it }
        Text("${ranks.topics.count { it.tier >= 0 }}/${ranks.topics.size} tópicos com colocação concluída")
        ranks.topics.filter { it.subject == subject }.forEach { topic ->
            Panel(topic.topic) {
                RankEmblem(topic.tier)
                Text(topic.name, style = MaterialTheme.typography.titleLarge)
                Text(if (topic.total == 0L) "Ainda sem questões" else "%.1f%% de acerto · %d questões".format(topic.accuracy, topic.total))
                if (topic.total < 20) Text("Mais ${20 - topic.total} questões para concluir a colocação")
                else if (topic.tier < 7) Text("Próximo: ${rankNames[topic.tier + 1]} · ≥${sampleLimits[topic.tier + 1]} questões e ≥${accuracyLimits[topic.tier + 1]}% de acerto")
            }
        }
        Text("${ranks.ignored} questões sem correspondência única com o edital ficam fora dos elos. Anki não conta. Todo o histórico válido é considerado; editar registros recalcula o elo.")
        Panel("Regras propostas de gamificação") {
            rankNames.forEachIndexed { i, name -> Text("$name · físico ${repLimits[i]} reps · tópico ≥${sampleLimits[i]} questões / ≥${accuracyLimits[i]}%") }
        }
    }
}
