package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

class HealthAnalyticsTest {
    private fun row(id: Long, day: String, group: String, exercise: String, reps: Int = 0,
                    volume: Int = 0, count: Int = 0) = TrainingRecord(
        id = id, data = day, horario = "12:00:00", group = group, exercicio = exercise, repeticoes = reps,
        extras = buildJsonObject { if (volume > 0) { put("volume_ml", volume); put("quantidade", count) } }
    )

    @Test fun waterIsVolumeTimesCountOnSelectedDay() {
        val day = LocalDate.parse("2026-09-23")
        val rows = listOf(row(1, "2026-09-23", "Nutrição", "Água", volume=750, count=5),
            row(2, "2026-09-22", "Nutrição", "Água", volume=500, count=2))
        assertEquals(3750, dailyWaterMl(rows, day))
    }

    @Test fun overnightSleepUsesWakeDay() {
        assertEquals(480, sleepMinutes("23:00", "07:00"))
    }

    @Test fun exerciseSummaryUsesDistinctTrainedDays() {
        val rows = listOf(row(1, "2026-09-21", "Peitoral", "Flexão", reps=10),
            row(2, "2026-09-21", "Peitoral", "Flexão", reps=20),
            row(3, "2026-09-22", "Peitoral", "Flexão", reps=30))
        val summary = trainingSnapshot(rows, "Flexão")!!
        assertEquals(2, summary.days)
        assertEquals(30.0, summary.meanRepsPerDay, 0.001)
        assertEquals(30, summary.record.repeticoes)
        val category = categorySnapshot(rows, "Peitoral")!!
        assertEquals(2, category.days)
        assertEquals(30.0, category.meanRepsPerDay, 0.001)
    }

    @Test fun cardioRecordUsesDistanceAndChangesWithExercise() {
        val rows = listOf(row(1, "2026-09-21", "Peitoral", "Flexão", reps=20),
            row(2, "2026-09-22", "Cardio", "Caminhada").copy(distanceKm=2.5),
            row(3, "2026-09-23", "Cardio", "Caminhada").copy(distanceKm=3.5))
        val flexao = trainingMeasureSnapshot(rows, "Flexão")!!
        val caminhada = trainingMeasureSnapshot(rows, "Caminhada")!!
        assertEquals("rep", flexao.unit)
        assertEquals(20.0, flexao.record, 0.001)
        assertEquals("km", caminhada.unit)
        assertEquals(3.5, caminhada.record, 0.001)
        assertEquals(3.0, caminhada.meanPerDay, 0.001)
    }

    @Test fun recommendationAvoidsRecentlyTrainedGroups() {
        val today = LocalDate.parse("2026-09-23")
        val rows = listOf(row(1, "2026-09-22", "Peitoral", "Flexão", reps=20),
            row(2, "2026-09-22", "Costas", "Barra Fixa", reps=8))
        assertTrue(suggestTraining(rows, today).contains("pernas"))
    }
}
