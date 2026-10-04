package com.matheussantos.solem.domain

import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import kotlinx.serialization.json.*
import kotlin.math.floor

const val MEAL_CONSENT = "meal-photo-openrouter-2026-10-v2"
@Serializable data class MealNutrients(val kcal: Double = 0.0,
    @SerialName("protein_g") val protein: Double = 0.0,
    @SerialName("carbs_g") val carbs: Double = 0.0,
    @SerialName("fat_g") val fat: Double = 0.0,
    @SerialName("fiber_g") val fiber: Double = 0.0)
@Serializable data class MealReference(val id: String, val name: String, val description: String,
    @SerialName("source_url") val sourceUrl: String, val per100: MealNutrients)
@Serializable data class MealFood(val name: String, @SerialName("food_id") val foodId: String = "",
    val grams: Double = 0.0, val confidence: String = "low")
@Serializable data class MealEstimate(val items: List<MealFood>, val totals: MealNutrients,
    val missing: Int, val complete: Boolean, val estimated: Boolean = true,
    val basis: String = "USDA FoodData Central / SR Legacy",
    @SerialName("catalog_version") val catalogVersion: String = "sr-2018-solem-1")
val mealJson = Json { ignoreUnknownKeys = true; encodeDefaults = true }
private fun decimal(value: Double) = floor(value * 10 + 0.5) / 10
fun calculateMeal(items: List<MealFood>, catalog: List<MealReference>): MealEstimate {
    require(items.size in 1..12) { "Mantenha entre 1 e 12 alimentos." }
    val checked = items.map {
        require(it.name.isNotBlank() && it.name.length <= 80 && it.grams.isFinite() && it.grams in 0.0..2000.0) {
            "Confira o alimento e a porção (0 a 2000 g)."
        }
        it.copy(name=it.name.trim(), grams=decimal(it.grams),
            foodId=it.foodId.takeIf { id -> catalog.any { food -> food.id==id } }.orEmpty(),
            confidence=it.confidence.takeIf { level -> level in listOf("high","medium","low") } ?: "low")
    }
    var missing=0; var kcal=0.0; var protein=0.0; var carbs=0.0; var fat=0.0; var fiber=0.0
    checked.forEach { item ->
        val food=catalog.firstOrNull { it.id==item.foodId }
        if(food==null || item.grams==0.0) missing++
        else {
            val scale=item.grams/100
            kcal+=food.per100.kcal*scale; protein+=food.per100.protein*scale
            carbs+=food.per100.carbs*scale; fat+=food.per100.fat*scale; fiber+=food.per100.fiber*scale
        }
    }
    return MealEstimate(checked,MealNutrients(decimal(kcal),decimal(protein),decimal(carbs),decimal(fat),decimal(fiber)),missing,missing==0)
}
fun photoMealDetails(kind: String, items: List<MealFood>, catalog: List<MealReference>): JsonObject {
    val estimate=calculateMeal(items,catalog)
    return buildJsonObject {
        put("tipo_refeicao",kind); put("input_method","photo_reviewed")
        put("saudaveis",buildJsonArray { estimate.items.forEach { add(JsonPrimitive(it.name)) } })
        put("ocasionais",JsonArray(emptyList()))
        put("nutrition",mealJson.encodeToJsonElement(estimate))
    }.also { require(it.toString().toByteArray(Charsets.UTF_8).size<=3800) { "Reduza o número ou o tamanho dos nomes dos alimentos." } }
}
