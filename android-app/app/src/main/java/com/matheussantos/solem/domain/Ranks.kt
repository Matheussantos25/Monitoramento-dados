package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import java.time.LocalDate

val rankNames = listOf("Ferro", "Bronze", "Prata", "Ouro", "Platina", "Esmeralda", "Diamante", "Mestre")
val repLimits = listOf(0L, 100L, 500L, 1500L, 3500L, 7000L, 12000L, 20000L)
val accuracyLimits = listOf(0, 40, 50, 60, 70, 80, 90, 95)
val sampleLimits = listOf(20, 20, 30, 40, 60, 80, 120, 200)
data class TopicRank(val subject: String, val topic: String, val correct: Long, val total: Long) {
    val accuracy get() = if (total > 0) correct * 100.0 / total else 0.0
    val tier get() = (0..7).lastOrNull { total >= sampleLimits[it] && accuracy >= accuracyLimits[it] } ?: -1
    val name get() = rankNames.getOrNull(tier) ?: "Em colocação"
}
data class Ranks(val reps: Long, val topics: List<TopicRank>, val ignored: Long) {
    val tier get() = repLimits.indexOfLast { reps >= it }
}
fun calculateRanks(rows: List<TrainingRecord>, topics: Map<String, List<String>>, today: LocalDate): Ranks {
    val stats = topics.flatMap { (d, ts) -> ts.filterNot { "Simulado" in it }.map { (d to it) to longArrayOf(0, 0) } }.toMap()
    var reps = 0L
    var ignored = 0L
    rows.distinctBy { it.id }.forEach { row ->
        val day = runCatching { LocalDate.parse(row.data.take(10)) }.getOrNull() ?: return@forEach
        if (day > today) return@forEach
        if (row.group !in listOf("Estudos", "Nutrição", "Métricas", "")) reps += row.repeticoes.coerceAtLeast(0).toLong()
        if (row.group != "Estudos" || row.extra("fonte_questoes") == "Anki") return@forEach
        fun count(key: String): Long = row.number(key).let { if (it.isFinite()) it.coerceAtLeast(0.0).toLong() else 0L }
        val correct = count("q_certas")
        val wrong = count("q_erradas")
        val topic = row.extra("topico_edital").ifBlank { row.extra("topico") }
        val target = stats[row.exercicio to topic]
        if (target == null) ignored += correct + wrong else { target[0] += correct; target[1] += wrong }
    }
    return Ranks(reps, stats.map { (key, values) -> TopicRank(key.first, key.second, values[0], values.sum()) }, ignored)
}
