package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.json.*
import java.time.LocalDate
import java.time.ZoneOffset
import java.time.temporal.ChronoUnit
import kotlin.math.pow

fun today(): LocalDate = LocalDate.now(ZoneOffset.ofHours(-3))
fun TrainingRecord.extra(key: String) = (extras[key] as? JsonPrimitive)?.contentOrNull.orEmpty()
fun TrainingRecord.number(key: String) = extra(key).toDoubleOrNull()?.takeIf { it.isFinite() && it >= 0 } ?: 0.0
fun TrainingRecord.studyMinutes() = if (extras.containsKey("tempo_segundos_exato") && extras["tempo_segundos_exato"] != JsonNull) number("tempo_segundos_exato") / 60 else durationMinutes.toDouble()
fun TrainingRecord.isWorkout() = group.isNotBlank() && group !in listOf("Estudos", "Nutrição", "Métricas")
fun filterPeriod(rows: List<TrainingRecord>, period: String, now: LocalDate = today()) = rows.filter {
    val date = runCatching { LocalDate.parse(it.data.take(10)) }.getOrNull()
    date != null && when (period) {
        "Hoje" -> date == now
        "Últimos 7 Dias" -> date >= now.minusDays(7)
        "Últimos 30 Dias" -> date >= now.minusDays(30)
        "Este Ano" -> date.year == now.year
        else -> true
    }
}
fun nextSubject(rows: List<TrainingRecord>, catalog: Catalog): String {
    val last = rows.filter { it.group == "Estudos" && it.exercicio in catalog.route }
        .maxWithOrNull(compareBy<TrainingRecord> { it.data }.thenBy { it.horario })
    return catalog.route[(catalog.route.indexOf(last?.exercicio) + 1) % catalog.route.size]
}
fun weakestTopic(rows: List<TrainingRecord>, subject: String, catalog: Catalog): String {
    val choices = catalog.topics[subject].orEmpty().filterNot { "Simulado" in it }
    if (choices.isEmpty()) return "Geral"
    val stats = linkedMapOf<String, Pair<Double, Double>>()
    rows.filter { it.group == "Estudos" && it.exercicio == subject }.forEach { row ->
        val date = runCatching { LocalDate.parse(row.data.take(10)) }.getOrDefault(today())
        val weight = 0.5.pow(ChronoUnit.DAYS.between(date, today()).coerceAtLeast(0) / 7.0)
        row.extra("topico_edital").ifBlank { "Geral" }.split(",").forEach {
            val old = stats[it.trim()] ?: (0.0 to 0.0)
            stats[it.trim()] = old.first + row.number("q_certas") * weight to old.second + (row.number("q_certas") + row.number("q_erradas")) * weight
        }
    }
    return choices.firstOrNull { it !in stats } ?: stats.filter { it.key in choices && it.value.second > 0 }
        .minByOrNull { it.value.first / it.value.second }?.key ?: choices.first()
}
