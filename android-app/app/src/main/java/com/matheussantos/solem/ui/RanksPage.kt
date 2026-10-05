package com.matheussantos.solem.ui

import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.domain.*

@Composable fun RanksPage(rows: List<TrainingRecord>, catalog: Catalog) {
    val ranks = calculateRanks(rows, catalog.topics, today())
    var subject by rememberSaveable { mutableStateOf(catalog.topics.keys.first()) }
    Page("Sua jornada ranqueada") {
        Text("Elos pessoais derivados do histórico. Não são avaliação de saúde nem previsão de aprovação.")
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
        Choice(if (catalog.generic) "Área de estudo" else "Disciplina do edital", subject, catalog.topics.keys.toList()) { subject = it }
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
        Text("${ranks.ignored} questões sem correspondência única com ${if (catalog.generic) "os tópicos" else "o edital"} ficam fora dos elos. Anki não conta. Todo o histórico válido é considerado; editar registros recalcula o elo.")
        Panel("Regras propostas de gamificação") {
            rankNames.forEachIndexed { i, name -> Text("$name · físico ${repLimits[i]} reps · tópico ≥${sampleLimits[i]} questões / ≥${accuracyLimits[i]}%") }
        }
    }
}
