package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import java.time.LocalDate
import kotlin.math.floor

@Serializable data class WeeklyPlanDefinition(
    val version: Int, @SerialName("starts_on") val startsOn: String,
    @SerialName("lookback_days") val lookbackDays: Int,
    @SerialName("history_factor") val historyFactor: Double,
    val exercises: Map<String, PlanExercise>, val days: List<PlanWeekday>, val cycle: TrainingCycleDefinition? = null
)
@Serializable data class PlanExercise(val exercise: String, val unit: String, val field: String,
    val minimum: Int, val maximum: Int, val step: Int, val sets: Int,
    @SerialName("rest_seconds") val restSeconds: Int, val note: String = "", val baseId: String = "")
@Serializable data class PlanWeekday(val title: String, val exercises: List<String>, val minutes: String)
data class PlanGoal(val spec: PlanExercise, val target: Int, val value: Double, val historyDays: Int) {
    val fraction get() = (value / target).coerceIn(0.0, 1.0)
}
data class WorkoutPlanDay(val date: LocalDate, val title: String, val duration: String,
    val goals: List<PlanGoal>, val active: Boolean, val cycle: Boolean = false,
    val cycleWeek: Int = 0, val stage: Int = 0, val phase: String = "", val held: Boolean = false,
    val completed: Boolean = false) {
    val recovery get() = active && goals.isEmpty()
    val percent: Int? get() = if(goals.isEmpty()) null else floor(goals.map {it.fraction}.average()*100 + 1e-7).toInt()
}

fun weeklyPlanDay(records: List<TrainingRecord>, day: LocalDate, definition: WeeklyPlanDefinition,
    enabled: Boolean = true): WorkoutPlanDay {
    definition.cycle?.let { if(enabled && day >= LocalDate.parse(it.startsOn)) return trainingCycleDay(records, day, it) }
    val weekday = definition.days[day.dayOfWeek.value - 1]
    val monday = day.minusDays((day.dayOfWeek.value - 1).toLong())
    val active = enabled && day >= LocalDate.parse(definition.startsOn)
    val rows = records.distinctBy {it.id}.filter { it.isWorkout() && runCatching {LocalDate.parse(it.data.take(10))}.isSuccess }
    val goals = if(!active) emptyList() else weekday.exercises.map { key ->
        val spec = definition.exercises.getValue(key)
        fun amount(row: TrainingRecord): Double {
            val number = if(spec.field == "isometria_segundos") row.number(spec.field) else row.repeticoes.toDouble()
            return number.takeIf {it.isFinite() && it > 0} ?: 0.0
        }
        val relevant = rows.filter {it.exercicio == spec.exercise}
        val previous = relevant.filter {
            val date = LocalDate.parse(it.data.take(10))
            date >= monday.minusDays(definition.lookbackDays.toLong()) && date < monday
        }.groupBy {it.data.take(10)}.values.map { group -> group.sumOf(::amount) }.filter {it > 0}.sorted()
        val middle = previous.size/2
        val median = if(previous.isEmpty()) 0.0 else if(previous.size%2 == 0) (previous[middle-1]+previous[middle])/2 else previous[middle]
        val target = (if(previous.size >= 2) floor(median*definition.historyFactor/spec.step).toInt()*spec.step else spec.minimum)
            .coerceIn(spec.minimum, spec.maximum)
        PlanGoal(spec, target, relevant.filter {it.data.take(10) == day.toString()}.sumOf(::amount), previous.size)
    }
    return WorkoutPlanDay(day, weekday.title, weekday.minutes, goals, active)
}

fun baseWorkoutPercent(rows: List<TrainingRecord>, day: LocalDate, settings: DashboardPreferences,
    generic: Boolean, definition: WeeklyPlanDefinition? = null): Int? {
    val missions = dailyMissions(rows, emptyList(), settings, generic, false, day, definition).filter {it.destination == 1}
    return if(missions.isEmpty()) null else floor(missions.map {it.fraction.toDouble()}.average()*100 + 1e-5).toInt()
}
