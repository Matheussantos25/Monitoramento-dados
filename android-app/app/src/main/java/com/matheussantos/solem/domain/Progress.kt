package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import java.time.LocalDate
import java.time.ZoneId

data class Progress(val xp: Int, val streak: Int, val days: Int, val workoutDays: Int, val studyDays: Int)

/** Same history-derived daily XP rules as solem_progress.py; no counter is persisted. */
fun calculateProgress(records: List<TrainingRecord>, today: LocalDate = LocalDate.now(ZoneId.of("America/Sao_Paulo"))): Progress {
    val perDay = mutableMapOf<LocalDate, MutableSet<String>>()
    records.forEach { record ->
        val date = runCatching { LocalDate.parse(record.data.take(10)) }.getOrNull() ?: return@forEach
        if (date > today) return@forEach
        val category = when (record.group) {
            "Estudos" -> if (record.durationMinutes > 0 || record.repeticoes > 0 || listOf("tempo_video", "q_certas", "q_erradas", "tempo_segundos_exato").any { record.number(it) > 0 }) "study" else null
            "Nutrição" -> if (record.healthyFood.isNotBlank() || record.junkFood.isNotBlank()) "food" else null
            "Métricas", "" -> null
            else -> if (record.repeticoes > 0 || record.durationMinutes > 0 || record.distanceKm > 0 || record.number("isometria_segundos") > 0) "workout" else null
        }
        if (category != null) perDay.getOrPut(date) { mutableSetOf() }.add(category)
    }
    val xp = perDay.values.sumOf { categories ->
        categories.sumOf { if (it == "food") 10 else 30 } + if (categories.containsAll(setOf("workout", "study"))) 15 else 0
    }
    var streak = 0; var cursor = if (perDay.containsKey(today)) today else today.minusDays(1)
    while (perDay.containsKey(cursor)) { streak++; cursor = cursor.minusDays(1) }
    return Progress(xp, streak, perDay.size, perDay.count { it.value.contains("workout") }, perDay.count { it.value.contains("study") })
}
