package com.matheussantos.solem.domain
import org.junit.Assert.*
import org.junit.Test
import kotlinx.serialization.json.decodeFromJsonElement

class CumulativeMealTest {
    private val foods=listOf(MealFood("Feijão","175200"),MealFood("Arroz","169757"),MealFood("Outro"))
    private val catalog:List<MealReference> = mealJson.decodeFromString(javaClass.getResource("/nutrition_catalog.json")!!.readText())
    @Test fun differencesTareAndEditing() {
        listOf(
            MealWeighing(baseline=0.0,readings=listOf(60.0,128.0,201.0)) to listOf(60.0,68.0,73.0),
            MealWeighing(baseline=0.0,readings=listOf(69.0,128.0,201.0)) to listOf(69.0,59.0,73.0),
            MealWeighing(baseline=250.0,readings=listOf(310.0,378.0,451.0)) to listOf(60.0,68.0,73.0),
            MealWeighing(baseline=0.0,readings=listOf(60.5,128.5,201.7)) to listOf(60.5,68.0,73.2),
            MealWeighing(baseline=0.0,readings=listOf(60.0,60.0,201.0)) to listOf(60.0,0.0,141.0)
        ).forEach {(weighing,expected) ->assertEquals(expected,cumulativeMealItems(foods,weighing).map {it.grams})}
        assertTrue(foods.all {it.grams==0.0})
    }
    @Test fun rejectsNegativeNonFiniteAndInconsistentReadings() {
        listOf(
            MealWeighing(baseline=-1.0,readings=listOf(60.0,128.0,201.0)),
            MealWeighing(baseline=10001.0,readings=listOf(60.0,128.0,201.0)),
            MealWeighing(baseline=Double.NaN,readings=listOf(60.0,128.0,201.0)),
            MealWeighing(readings=listOf(60.0,50.0,201.0)),
            MealWeighing(readings=listOf(60.0,128.0,Double.POSITIVE_INFINITY)),
            MealWeighing(readings=listOf(60.0,128.0,2200.0)),
            MealWeighing(readings=listOf(60.0,128.0))
        ).forEach {assertTrue(runCatching {photoMealDetails("Almoço",foods,catalog,true,it)}.isFailure)}
    }
    @Test fun payloadRestoresReadingsAndNutritionUsesNetWeight() {
        val weighing=MealWeighing(baseline=250.0,readings=listOf(310.0,378.0,451.0))
        val payload=photoMealDetails("Almoço",foods,catalog,true,weighing)
        assertEquals(weighing,mealJson.decodeFromJsonElement<MealWeighing>(payload.getValue("weighing")))
        val result=mealJson.decodeFromJsonElement<MealEstimate>(payload.getValue("nutrition"))
        assertEquals(174.2,result.totals.kcal,.01)
        assertFalse(result.complete)
        assertEquals(listOf(60.0,68.0,73.0),result.items.map {it.grams})
    }
}
