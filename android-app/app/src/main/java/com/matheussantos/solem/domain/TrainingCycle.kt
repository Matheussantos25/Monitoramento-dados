package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import java.time.LocalDate
import java.time.temporal.ChronoUnit
import kotlin.math.floor

@Serializable data class TrainingCycleDefinition(
    @SerialName("starts_on") val startsOn: String, val weeks: Int,
    val labels: List<String>, val days: List<PlanWeekday>, val exercises: Map<String, CycleExercise>)
@Serializable data class CycleExercise(val exercise: String, val unit: String, val field: String,
    val sets: List<Int>, @SerialName("per_set") val perSet: List<Int>,
    @SerialName("rest_seconds") val restSeconds: Int, val minimum: Int, val maximum: Int,
    val history: Boolean, @SerialName("base_id") val baseId: String, val note: String)

/** Goals are derived without changing records or saved preferences. Same rules as the web. */
fun trainingCycleDay(records: List<TrainingRecord>, day: LocalDate, cycle: TrainingCycleDefinition, previewStage: Int? = null): WorkoutPlanDay {
    val start = LocalDate.parse(cycle.startsOn)
    val index = Math.floorDiv(ChronoUnit.DAYS.between(start, day).toInt(), 7)
    if(index !in 0 until cycle.weeks) return WorkoutPlanDay(day,
        if(day >= start) "Ciclo concluído · revise antes de reiniciar" else "Ciclo começa em ${cycle.startsOn}",
        "", emptyList(), false, cycle=true, completed=day >= start)
    val rows = records.distinctBy {it.id}.filter {it.isWorkout() && runCatching {LocalDate.parse(it.data.take(10))}.isSuccess}
    fun amount(row: TrainingRecord, spec: CycleExercise): Double {
        val value = when(spec.field) {
            "isometria_segundos" -> row.number(spec.field)
            "distancia_km" -> row.distanceKm
            else -> row.repeticoes.toDouble()
        }
        return value.takeIf {it.isFinite() && it > 0} ?: 0.0
    }
    fun baseline(spec: CycleExercise): Triple<Int, Int, Double?> {
        val samples = rows.filter {
            val date = LocalDate.parse(it.data.take(10))
            it.exercicio == spec.exercise && date >= start.minusDays(28) && date < start && it.series in 2..8
        }.map {amount(it,spec)/it.series}.filter {it > 0 && it <= if(spec.unit == "seg") 180 else 30}.sorted()
        val mid = samples.size/2
        val median = if(samples.size < 2) null else if(samples.size%2 == 0) (samples[mid-1]+samples[mid])/2 else samples[mid]
        val base = if(spec.history && median != null) floor(median*.8).toInt().coerceIn(spec.minimum,spec.maximum) else spec.perSet[0]
        return Triple(base,samples.size,median)
    }
    fun goalsAt(date: LocalDate, stage: Int): List<PlanGoal> = cycle.days[date.dayOfWeek.value-1].exercises.map {key ->
        var spec = cycle.exercises.getValue(key)
        var baseline = baseline(spec)
        val fallback = key == "pull" && (baseline.third == null || baseline.third!! * .8 < 3)
        if(fallback) { spec = cycle.exercises.getValue("row"); baseline = baseline(spec) }
        val perSet = baseline.first + spec.perSet[stage] - spec.perSet[0]
        val names = if(key == "walk") listOf("Caminhada","Corrida") else listOf(spec.exercise)
        val value = rows.filter {it.data.take(10)==date.toString() && it.exercicio in names}.sumOf {amount(it,spec)}
        val note = (if(fallback) "Sem referência suficiente por série na barra: remada como alternativa. " else "") + spec.note
        PlanGoal(PlanExercise(spec.exercise,spec.unit,spec.field,spec.minimum,spec.maximum,1,spec.sets[stage],spec.restSeconds,note,spec.baseId),
            perSet*spec.sets[stage],value,baseline.second)
    }
    var stage = 0
    repeat(index) {previous ->
        val first = start.plusDays(previous*7L)
        val achieved = (0..6).count {offset ->
            val date = first.plusDays(offset.toLong())
            val goals = goalsAt(date,stage)
            date.dayOfWeek.value in listOf(1,3,5) && goals.isNotEmpty() && goals.all {it.fraction >= .8}
        }
        if(achieved >= 2) stage = (stage+1).coerceAtMost(2)
    }
    if(index == 3) stage = 3
    if(previewStage != null) stage = previewStage.coerceIn(0,3)
    val weekday = cycle.days[day.dayOfWeek.value-1]
    return WorkoutPlanDay(day,weekday.title,weekday.minutes,goalsAt(day,stage),true,true,index+1,stage+1,cycle.labels[stage],stage<index)
}
