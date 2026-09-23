package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import java.time.LocalDate
import java.time.YearMonth

data class JournalDay(val date: LocalDate, val study: Boolean, val workout: Boolean,
    val studyMinutes: Double, val workoutMinutes: Double, val reps: Long, val distance: Double,
    val activities: List<String>)

fun monthlyJournal(rows: List<TrainingRecord>, month: YearMonth, now: LocalDate = today()): List<JournalDay> {
    val byDay = rows.groupBy { runCatching { LocalDate.parse(it.data.take(10)) }.getOrNull() }
    return (1..month.lengthOfMonth()).map { day ->
        val date = month.atDay(day)
        val valid = byDay[date].orEmpty().filter { date <= now }
        val study = valid.filter { it.group == "Estudos" && (it.repeticoes > 0 || it.durationMinutes > 0 || listOf("tempo_video","q_certas","q_erradas","tempo_segundos_exato").any { key -> it.number(key) > 0 }) }
        val workout = valid.filter { it.isWorkout() && (it.repeticoes > 0 || it.durationMinutes > 0 || it.distanceKm > 0 || it.number("isometria_segundos") > 0) }
        JournalDay(date,study.isNotEmpty(),workout.isNotEmpty(),study.sumOf { it.studyMinutes().coerceAtLeast(0.0)+it.number("tempo_video") },
            workout.sumOf { it.durationMinutes.coerceAtLeast(0).toDouble()+it.number("isometria_segundos")/60 },
            workout.sumOf { it.repeticoes.coerceAtLeast(0).toLong() },workout.sumOf { it.distanceKm.coerceAtLeast(0.0) },(study+workout).map { it.exercicio })
    }
}
fun latestWeight(rows: List<TrainingRecord>, now: LocalDate = today()) = rows.filter {
    val day = runCatching { LocalDate.parse(it.data.take(10)) }.getOrNull()
    day != null && day <= now && it.bodyWeight.isFinite() && it.bodyWeight > 0
}.maxWithOrNull(compareBy<TrainingRecord> { it.data }.thenBy { it.horario }.thenBy { it.id })
