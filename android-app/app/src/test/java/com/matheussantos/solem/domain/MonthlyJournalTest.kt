package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate
import java.time.YearMonth

class MonthlyJournalTest {
    private val now=LocalDate.parse("2026-09-07")
    @Test fun leapYearHasAllDays() {
        val days=monthlyJournal(emptyList(),YearMonth.of(2024,2),now)
        assertEquals(29,days.size); assertEquals(4,days.first().date.dayOfWeek.value)
    }
    @Test fun recordedTimeIsNotEstimatedFromReps() {
        val rows=listOf(TrainingRecord(1,"2026-09-02","12:00:00","Peitoral","Flexão",repeticoes=20),
            TrainingRecord(2,"2026-09-02","13:00:00","Estudos","Anki",durationMinutes=60,extras=buildJsonObject {put("tempo_segundos_exato",90);put("tempo_video",10)}))
        val day=monthlyJournal(rows,YearMonth.of(2026,9),now)[1]
        assertTrue(day.study && day.workout);assertEquals(11.5,day.studyMinutes,0.0001)
        assertEquals(0.0,day.workoutMinutes,0.0001);assertEquals(20L,day.reps)
    }
    @Test fun futureEmptyAndWeightDoNotCount() {
        val rows=listOf(TrainingRecord(1,"2026-09-02","12:00:00","Estudos","Estudo"),
            TrainingRecord(2,"2026-09-08","12:00:00","Pernas","Agachamento",repeticoes=20),
            TrainingRecord(3,"2026-09-02","12:00:00","Métricas","Peso Diário",bodyWeight=70.0))
        assertFalse(monthlyJournal(rows,YearMonth.of(2026,9),now).any { it.study || it.workout })
    }
    @Test fun latestWeightMustBePositiveAndNotFuture() {
        val valid=TrainingRecord(1,"2026-09-02","12:00:00","Métricas","Peso",bodyWeight=70.0)
        assertEquals(valid,latestWeight(listOf(valid,valid.copy(id=2,data="2026-10-01",bodyWeight=90.0),valid.copy(id=3,data="2026-09-03",bodyWeight=0.0)),now))
        assertNull(latestWeight(emptyList(),now))
    }
}
