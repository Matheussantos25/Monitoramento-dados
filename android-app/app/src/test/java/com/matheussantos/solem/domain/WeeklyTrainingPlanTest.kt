package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class WeeklyTrainingPlanTest {
    private val day = LocalDate.of(2026,10,19)
    private val definition = Json.decodeFromString<WeeklyPlanDefinition>(javaClass.getResource("/weekly_training_plan.json")!!.readText())
    private fun row(id: Long, date: LocalDate=day, name: String="Abdominal Levantada", reps: Int=12, seconds: Int=0) =
        TrainingRecord(id,date.toString(),"08:00:00","Abdominal",name,repeticoes=reps,
            extras=buildJsonObject {put("isometria_segundos",seconds)})

    @Test fun morningSleepStaysOnSameDate() {
        val result = sleepPeriod(day,"02:00","08:00")
        assertEquals(day,result.bedDay); assertEquals(day,result.wakeDay); assertEquals(360,result.minutes)
    }
    @Test fun nightSleepCrossesYearBoundary() {
        assertEquals(LocalDate.of(2026,12,31),sleepPeriod(LocalDate.of(2027,1,1),"23:00","07:00").bedDay)
    }
    @Test fun explicitDatesRejectNegativeOrOverlongDuration() {
        assertTrue(runCatching {sleepPeriod(day,"02:00","08:00","previous")}.isFailure)
        assertTrue(runCatching {sleepPeriod(day,"23:00","07:00","same")}.isFailure)
        assertTrue(runCatching {sleepPeriod(day,"08:00","08:00")}.isFailure)
    }
    @Test fun planDoesNotChangeTargetsAfterTodaysRegistration() {
        val rows=listOf(row(1,day.minusDays(3),reps=20),row(2,day.minusDays(5),reps=40))
        val before=weeklyPlanDay(rows,day,definition)
        val after=weeklyPlanDay(rows+row(3,reps=900)+row(4,day.plusDays(20),reps=1000),day,definition)
        assertEquals(20,before.goals.first().target)
        assertEquals(before.goals.map {it.target},after.goals.map {it.target})
        assertEquals(50,after.percent)
    }
    @Test fun editsDeletionAndDuplicatesRecomputeRealProgress() {
        val a=row(1,reps=6); val b=row(2,reps=6); val plank=row(3,name="Prancha",seconds=30)
        assertEquals(100,weeklyPlanDay(listOf(a,b,plank),day,definition).percent)
        assertEquals(75,weeklyPlanDay(listOf(a,plank),day,definition).percent)
        assertEquals(62,weeklyPlanDay(listOf(a.copy(repeticoes=3),plank),day,definition).percent)
        val half=row(4,name="Prancha",reps=999,seconds=15)
        assertEquals(25,weeklyPlanDay(listOf(half,half),day,definition).percent)
    }
    @Test fun recoveryAndDisabledPlanDoNotPretendToBeComplete() {
        val recovery=weeklyPlanDay(emptyList(),day.plusDays(2),definition)
        assertTrue(recovery.recovery); assertNull(recovery.percent)
        assertFalse(weeklyPlanDay(emptyList(),day.minusDays(1),definition).active)
        assertFalse(weeklyPlanDay(emptyList(),day,definition,false).active)
        assertEquals(0,weeklyPlanDay(emptyList(),day,definition).percent)
    }
    @Test fun baseGoalsAreUntouchedAndSeparate() {
        val settings=DashboardPreferences(pushups=100,squats=100)
        assertEquals(0,baseWorkoutPercent(listOf(row(1,reps=999)),day,settings,false))
        assertEquals(100,settings.pushups)
        assertEquals(100,settings.squats)
    }
}
