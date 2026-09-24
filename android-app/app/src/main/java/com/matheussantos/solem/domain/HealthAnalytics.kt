package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import java.time.LocalDate
import java.time.LocalTime
import java.time.temporal.ChronoUnit
import java.text.DecimalFormat
import java.text.DecimalFormatSymbols
import java.util.Locale

private val mainGroups = listOf("Peitoral", "Costas", "Pernas", "Abdominal")

fun dailyWaterMl(rows: List<TrainingRecord>, day: LocalDate): Int = rows.filter {
    it.data.take(10) == day.toString() && it.group == "Nutrição" && it.exercicio == "Água"
}.sumOf { row ->
    val size = row.number("volume_ml").toInt()
    val count = row.number("quantidade").toInt()
    if (size in 1..5000 && count in 1..50) size * count else 0
}

fun sleepMinutes(bed: String, wake: String): Int {
    val start = LocalTime.parse(bed)
    val end = LocalTime.parse(wake)
    val minutes = (ChronoUnit.MINUTES.between(start, end).toInt() + 1440) % 1440
    require(minutes in 1..960) { "Informe um período de sono de até 16 horas." }
    return minutes
}

data class TrainingSnapshot(val last: TrainingRecord, val record: TrainingRecord, val days: Int, val meanRepsPerDay: Double)

data class TrainingMeasureSnapshot(val unit: String, val last: Double, val record: Double,
    val days: Int, val meanPerDay: Double, val lastDay: String)

fun formatOneDecimal(value: Double): String =
    DecimalFormat("0.#", DecimalFormatSymbols(Locale.forLanguageTag("pt-BR"))).format(value)

fun trainingMeasureSnapshot(rows: List<TrainingRecord>, exercise: String, fields: List<String>): TrainingMeasureSnapshot? {
    val matches = rows.filter { it.isWorkout() && it.exercicio == exercise &&
        runCatching { LocalDate.parse(it.data.take(10)) }.isSuccess }
    if (matches.isEmpty()) return null
    val candidates: List<Pair<String, (TrainingRecord) -> Double>> = when {
        "isometria_segundos" in fields -> listOf("seg" to { it.number("isometria_segundos") }, "rep" to { it.repeticoes.toDouble() })
        "distancia_km" in fields -> listOf("km" to { it.distanceKm }, "min" to { it.durationMinutes.toDouble() })
        fields == listOf("duracao_min") -> listOf("min" to { it.durationMinutes.toDouble() })
        else -> listOf("rep" to { it.repeticoes.toDouble() }, "min" to { it.durationMinutes.toDouble() },
            "seg" to { it.number("isometria_segundos") }, "km" to { it.distanceKm })
    }
    val (unit, measure) = candidates.firstOrNull { (_, value) -> matches.any { value(it) > 0 } } ?: candidates.first()
    val last = matches.maxWith(compareBy<TrainingRecord> { it.data }.thenBy { it.horario })
    val byDay = matches.groupBy { it.data.take(10) }
    return TrainingMeasureSnapshot(unit, measure(last), matches.maxOf(measure), byDay.size,
        matches.sumOf(measure) / byDay.size, last.data.take(10))
}

fun trainingSnapshot(rows: List<TrainingRecord>, exercise: String): TrainingSnapshot? {
    val matches = rows.filter { it.isWorkout() && it.exercicio == exercise && runCatching { LocalDate.parse(it.data.take(10)) }.isSuccess }
    if (matches.isEmpty()) return null
    val byDay = matches.groupBy { it.data.take(10) }
    return TrainingSnapshot(
        last = matches.maxWith(compareBy<TrainingRecord> { it.data }.thenBy { it.horario }),
        record = matches.maxBy { it.repeticoes },
        days = byDay.size,
        meanRepsPerDay = byDay.values.sumOf { dayRows -> dayRows.sumOf { it.repeticoes } }.toDouble() / byDay.size
    )
}

data class CategorySnapshot(val days: Int, val meanRepsPerDay: Double)

fun categorySnapshot(rows: List<TrainingRecord>, group: String): CategorySnapshot? {
    val matches = rows.filter { it.isWorkout() && it.group == group &&
        runCatching { LocalDate.parse(it.data.take(10)) }.isSuccess }
    if (matches.isEmpty()) return null
    val days = matches.groupBy { it.data.take(10) }
    return CategorySnapshot(days.size, matches.sumOf { it.repeticoes }.toDouble() / days.size)
}

fun suggestTraining(rows: List<TrainingRecord>, day: LocalDate = today()): String {
    val last = mainGroups.associateWith { group -> rows.filter { it.isWorkout() && it.group == group }
        .mapNotNull { runCatching { LocalDate.parse(it.data.take(10)) }.getOrNull() }
        .filter { it <= day }.maxOrNull() }
    val group = mainGroups.minWith(compareBy<String> { last[it] ?: LocalDate.MIN }.thenBy { mainGroups.indexOf(it) })
    val ago = last[group]?.let { ChronoUnit.DAYS.between(it, day) }
    if (ago != null && ago < 2) return "Os grupos principais aparecem treinados recentemente. Considere descanso ou atividade leve."
    val name = mapOf("Peitoral" to "empurrar", "Costas" to "puxar", "Pernas" to "pernas", "Abdominal" to "core").getValue(group)
    return "Sugestão com base no histórico: $name. Ajuste à recuperação e à técnica."
}
