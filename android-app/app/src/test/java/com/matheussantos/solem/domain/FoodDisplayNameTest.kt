package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class FoodDisplayNameTest {
    private val catalog: List<MealReference> = mealJson.decodeFromString(javaClass.getResource("/nutrition_catalog.json")!!.readText())

    @Test fun aliasesAreUniqueAndPreserveCustomNames() {
        assertEquals(catalog.size,catalog.map { it.displayName }.distinct().size)
        assertEquals("Arroz",foodDisplayName(catalog.first().name,catalog))
        assertEquals("Feijão",catalog.first {it.id=="175200"}.displayName)
        assertEquals("Carne",catalog.first {it.id=="171793"}.displayName)
        assertEquals("Purê de batata",catalog.first {it.id=="170493"}.displayName)
        assertEquals("Arroz da minha receita",foodDisplayName("Arroz da minha receita",catalog))
    }

    @Test fun displayDoesNotChangeSavedPayloadOrTotals() {
        val ids=listOf("169757","175200","173424","169249","170493","171793")
        val items=ids.map {id -> MealFood(catalog.first {it.id==id}.name,id)}
        val weighing=MealWeighing(readings=listOf(170.0,323.0,371.0,386.0,457.0,491.0))
        val saved=photoMealDetails("Almoço",items,catalog,true,weighing)
        val before=saved.toString()
        assertEquals(listOf("Arroz","Feijão","Ovo cozido","Alface","Purê de batata","Carne"),items.map {foodDisplayName(it.name,catalog)})
        assertEquals(before,saved.toString())
        val totals=calculateMeal(cumulativeMealItems(items,weighing),catalog).totals
        assertEquals(644.7,totals.kcal,0.0)
        assertEquals(34.5,totals.protein,0.0)
    }
}
