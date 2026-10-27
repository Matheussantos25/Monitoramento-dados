package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.HealthEntry
import java.time.LocalDate
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test

class DailyNutritionTest {
    private val day=LocalDate.of(2026,10,27)
    private val refs: List<MealReference> = mealJson.decodeFromString(javaClass.getResource("/nutrition_catalog.json")!!.readText())
    private fun meal(id: String, grams: Double=44.0, date: LocalDate=day)=HealthEntry(id,date.toString(),"07:10:00","meal",
        photoMealDetails("Café da manhã",listOf(MealFood("Pão com manteiga","tbca-BRC0418A",grams)),refs,true))
    @Test fun addEditDeleteAndDayFilter() {
        val rows=mutableListOf(meal("a"),meal("b"),meal("yesterday",date=day.minusDays(1)),
            HealthEntry("weight",day.toString(),"10:00:00","weight"),
            HealthEntry("skip",day.toString(),"12:00:00","meal",buildJsonObject { put("sem_refeicao",true) }))
        var result=dailyNutrition(rows,day,refs)
        assertEquals(374.8,result.calories,0.01);assertEquals(6.4,result.protein,0.01)
        assertEquals(2,result.meals);assertFalse(result.partial)
        rows[1]=meal("b",100.0)
        assertEquals(613.4,dailyNutrition(rows,day,refs).calories,0.01)
        rows.removeAt(1)
        assertEquals(187.4,dailyNutrition(rows,day,refs).calories,0.01)
        assertEquals(0,dailyNutrition(emptyList(),day,refs).meals)
    }
    @Test fun missingAndInvalidNutritionRemainPartial() {
        val unknown=HealthEntry("legacy",day.toString(),"12:00:00","meal")
        val invalid=unknown.copy(id="bad",details=buildJsonObject {put("nutrition","bad")})
        val result=dailyNutrition(listOf(meal("a"),unknown,invalid),day,refs)
        assertTrue(result.partial);assertEquals(1,result.knownItems);assertEquals(3,result.meals)
        assertEquals(187.4,result.calories,0.01)
        assertEquals(0,dailyNutrition(listOf(unknown),day,refs).knownItems)
    }
}
