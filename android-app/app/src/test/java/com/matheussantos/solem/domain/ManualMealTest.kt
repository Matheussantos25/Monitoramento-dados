package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.HealthEntry
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class ManualMealTest {
    @Test fun skippedMealDiscardsFoodAndRemainsDistinctFromConsumed() {
        val value = manualMealDetails("Almoço", listOf("Arroz"), listOf("Pizza"), true)
        assertTrue(value.getValue("saudaveis").jsonArray.isEmpty())
        assertTrue(value.getValue("ocasionais").jsonArray.isEmpty())
        assertFalse(value.containsKey("nutrition"))
        assertTrue(HealthEntry("1", "2026-10-19", "12:00:00", "meal", value).skippedMeal)
    }
    @Test fun regularMealAndLegacyRowsRemainConsumed() {
        val value = manualMealDetails("Café da manhã", listOf("Batata-doce"), emptyList(), false)
        assertEquals("Batata-doce", value.getValue("saudaveis").jsonArray[0].jsonPrimitive.content)
        assertFalse(HealthEntry("1", "2026-10-19", "08:00:00", "meal", value).skippedMeal)
        assertFalse(HealthEntry("old", "2026-10-18", "08:00:00", "meal").skippedMeal)
    }
    @Test(expected=IllegalArgumentException::class) fun blankIsNotImplicitlySkipped() {
        manualMealDetails("Jantar", emptyList(), emptyList(), false)
    }
}
