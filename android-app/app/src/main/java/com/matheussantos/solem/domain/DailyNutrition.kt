package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.HealthEntry
import java.time.LocalDate
import kotlinx.serialization.json.decodeFromJsonElement

data class DailyNutrition(val calories: Double, val protein: Double,
    val meals: Int, val knownItems: Int, val partial: Boolean)

fun dailyNutrition(entries: List<HealthEntry>, day: LocalDate, references: List<MealReference>): DailyNutrition {
    val meals=entries.filter { it.day.take(10)==day.toString() && it.kind=="meal" && !it.skippedMeal }
    val calculated=meals.mapNotNull { row -> runCatching {
        row.details["nutrition"]?.let { mealJson.decodeFromJsonElement<MealEstimate>(it) }
            ?.let { calculateMeal(it.items,references) }
    }.getOrNull() }
    return DailyNutrition(calculated.sumOf { it.totals.kcal }, calculated.sumOf { it.totals.protein },
        meals.size, calculated.sumOf { it.items.size-it.missing },
        calculated.size!=meals.size || calculated.any { !it.complete })
}
