package com.matheussantos.solem.domain

import android.content.Context
import kotlinx.serialization.json.*

class Catalog(private val root: JsonObject) {
    constructor(context: Context) : this(Json.parseToJsonElement(context.assets.open("catalog.json").bufferedReader().use { it.readText() }).jsonObject)
    fun list(key: String) = root.getValue(key).jsonArray.map { it.jsonPrimitive.content }
    val groups = root.getValue("EXERCICIOS_PRESETADOS").jsonObject.mapValues { (_, value) -> value.jsonArray.map { it.jsonPrimitive.content } }
    val exercises = groups.values.flatten().sorted()
    val topics = root.getValue("TOPICOS_EDITAL").jsonObject.mapValues { (_, value) -> value.jsonArray.map { it.jsonPrimitive.content } }
    val subjects = list("DISCIPLINAS_ESTUDO").sorted()
    val decks = list("DECKS_ANKI")
    val sources = list("FONTES_QUESTOES")
    val route = list("ROTA_ESTRATEGICA")
    val periods = list("PERIODOS_DASHBOARD")
    val mealTypes = list("MEAL_TYPES")
    fun mealFoods(meal: String, selected: List<String> = emptyList()): List<String> {
        val catalog = list("ALIMENTOS_SAUDAVEIS")
        val suggestions = root.getValue("MEAL_FOODS").jsonObject[meal]?.jsonArray
            ?.map { it.jsonPrimitive.content }?.toSet()
        return ((if (suggestions == null) catalog else catalog.filter { it in suggestions }) + selected)
            .distinct().sortedWith(String.CASE_INSENSITIVE_ORDER)
    }
    fun group(exercise: String) = groups.entries.firstOrNull { exercise in it.value }?.key ?: "Outro"
    fun workoutFields(exercise: String): List<String> {
        val profile = root.getValue("WORKOUT_EXERCISE_PROFILES").jsonObject[exercise]?.jsonPrimitive?.content ?: "resistance"
        return root.getValue("WORKOUT_FIELD_PROFILES").jsonObject.getValue(profile).jsonArray.map { it.jsonPrimitive.content }
    }
}
