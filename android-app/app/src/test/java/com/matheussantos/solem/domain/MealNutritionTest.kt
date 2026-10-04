package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class MealNutritionTest {
    private val catalog: List<MealReference> = mealJson.decodeFromString(javaClass.getResource("/nutrition_catalog.json")!!.readText())
    private val rice=MealFood("Arroz","169757",150.0,"high")
    @Test fun sourceAndCalculations() {
        assertEquals(24,catalog.size)
        assertTrue(catalog.all { it.name.isNotBlank() && it.sourceUrl.startsWith("https://fdc.nal.usda.gov/") })
        val estimate=calculateMeal(listOf(rice),catalog)
        assertEquals(195.0,estimate.totals.kcal,0.01)
        assertEquals(4.0,estimate.totals.protein,0.01)
        assertTrue(estimate.complete)
        assertEquals(65.0,calculateMeal(listOf(rice.copy(grams=50.0)),catalog).totals.kcal,0.01)
    }
    @Test fun partialIsNotZeroCalories() {
        val result=calculateMeal(listOf(rice,rice.copy(foodId="unknown")),catalog)
        assertEquals(1,result.missing);assertFalse(result.complete)
        assertEquals(195.0,result.totals.kcal,0.01)
        assertFalse(calculateMeal(listOf(rice.copy(grams=0.0)),catalog).complete)
    }
    @Test fun badInputsAndPrivatePayload() {
        listOf(-1.0,2001.0,Double.NaN,Double.POSITIVE_INFINITY).forEach { grams ->
            assertTrue(runCatching { calculateMeal(listOf(rice.copy(grams=grams)),catalog) }.isFailure)
        }
        assertTrue(runCatching { calculateMeal(emptyList(),catalog) }.isFailure)
        assertTrue(runCatching { calculateMeal(List(13) { rice },catalog) }.isFailure)
        val payload=photoMealDetails("Almoço",listOf(rice),catalog).toString()
        assertFalse(payload.contains("image"));assertFalse(payload.contains("token"))
        assertTrue(payload.toByteArray().size<3800)
    }
}
