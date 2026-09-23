package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.json.JsonObject
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.LocalDate

class ProgressTest {
    @Test fun `xp is awarded once per category per day and bonus applies`() {
        val day = LocalDate.of(2026, 9, 5).toString()
        val records = listOf(
            record(1, day, "Peitoral", reps = 10), record(2, day, "Estudos", reps = 2),
            record(3, day, "Nutrição", healthy = "Banana"), record(4, day, "Peitoral", reps = 20)
        )
        val progress = calculateProgress(records, LocalDate.parse(day))
        assertEquals(85, progress.xp); assertEquals(1, progress.streak)
    }

    private fun record(id: Long, date: String, group: String, reps: Int = 0, healthy: String = "") = TrainingRecord(id, date, "12:00:00", group, "Teste", repeticoes = reps, healthyFood = healthy, extras = JsonObject(emptyMap()))
}
