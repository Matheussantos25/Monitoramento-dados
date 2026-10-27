package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class MealNutritionTest {
    private val catalog: List<MealReference> = mealJson.decodeFromString(javaClass.getResource("/nutrition_catalog.json")!!.readText())
    private val rice=MealFood("Arroz","169757",150.0,"high")
    @Test fun breadAndPotatoReferencesKeepWeights() {
        val breakfast=calculateMeal(listOf(MealFood("Pão com manteiga","tbca-BRC0418A",44.0)),catalog)
        assertTrue(breakfast.complete)
        assertEquals(187.4,breakfast.totals.kcal,0.01)
        assertEquals(3.2,breakfast.totals.protein,0.01)
        assertEquals("solem-nutrition-v3",breakfast.catalogVersion)
        val items=listOf(MealFood("Batata palha","yoki-batata-palha-tradicional"),
            MealFood("Arroz","169757"),MealFood("Frango","171477"),MealFood("Feijão","175200"))
        val weighing=MealWeighing(readings=listOf(12.0,144.0,314.0,481.0))
        val portions=cumulativeMealItems(items,weighing)
        assertEquals(listOf(12.0,132.0,170.0,167.0),portions.map { it.grams })
        val lunch=calculateMeal(portions,catalog)
        assertTrue(lunch.complete)
        assertEquals(757.1,lunch.totals.kcal,0.01)
        assertEquals(71.9,lunch.totals.protein,0.01)
        assertEquals(listOf(12.0,144.0,314.0,481.0),weighing.readings)
    }
    @Test fun weighedMealAndEdit() {
        val items=listOf(rice,MealFood("Frango","171477",100.0))
        val result=calculateMeal(items,catalog)
        assertEquals(360.0,result.totals.kcal,0.01)
        assertEquals(35.0,result.totals.protein,0.01)
        assertTrue(photoMealDetails("Almoço",items,catalog,true).toString().contains("weighed"))
        assertEquals(295.0,calculateMeal(listOf(rice.copy(grams=100.0),items[1]),catalog).totals.kcal,0.01)
        assertEquals(150.0,rice.grams,0.01)
    }
    @Test fun sourceAndCalculations() {
        assertEquals(39,catalog.size)
        assertEquals(24,catalog.count { it.id.all { c -> c.isDigit() } })
        assertTrue(catalog.all { it.name.isNotBlank() && (it.sourceUrl.startsWith("https://fdc.nal.usda.gov/") || it.sourceUrl.startsWith("https://nepa.unicamp.br/") || it.sourceUrl.startsWith("https://tbca.net.br/") || it.sourceUrl.startsWith("https://www.yoki.com.br/")) })
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
    @Test fun spokenBiscuitWithPunctuation() {
        val parsed=parseMealVoice("Biscoito recheado, 114 gramas, peso acumulado.",catalog)
        assertEquals(114.0,parsed.items!![0].grams,0.01)
    }
    @Test fun occasionalCumulativeMeal() {
        val items=listOf(MealFood("Biscoito recheado","taco-9"),MealFood("Chocolate ao leite","taco-495"))
        val portions=cumulativeMealItems(items,MealWeighing(readings=listOf(114.0,134.0)))
        val estimate=calculateMeal(portions,catalog)
        assertEquals(listOf(114.0,20.0),portions.map {it.grams})
        assertEquals(646.1,estimate.totals.kcal,0.01)
        assertEquals(8.7,estimate.totals.protein,0.01)
        assertTrue(estimate.basis.contains("TACO"))
        val details=photoMealDetails("Lanche da tarde",items,catalog,true,MealWeighing(readings=listOf(114.0,134.0)))
        assertEquals("[]",details["saudaveis"].toString())
        assertTrue(details["ocasionais"].toString().contains("Biscoito recheado"))
    }
}
