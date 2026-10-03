package com.matheussantos.solem.domain

import android.content.Context
import kotlinx.serialization.json.*

class Catalog(private val root: JsonObject, val generic: Boolean = false) {
    constructor(context: Context) : this(Json.parseToJsonElement(context.assets.open("catalog.json").bufferedReader().use { it.readText() }).jsonObject)
    constructor(context: Context, generic: Boolean) : this(accountCatalog(context, generic), generic)
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
    fun withStudyTopics(rows: List<com.matheussantos.solem.data.model.TrainingRecord>): Catalog {
        if (!generic) return this
        val updated = topics.mapValues { it.value.toMutableList() }.toMutableMap()
        rows.filter { it.group == "Estudos" && it.extra("fonte_questoes") != "Anki" && it.exercicio.isNotBlank() }.forEach { row ->
            val values = updated.getOrPut(row.exercicio) { mutableListOf() }
            row.extra("topico_edital").split(",").map { it.trim() }
                .filter { it.isNotBlank() && it !in listOf("Geral", "🎯 Simulado / Visão Geral") && it !in values }
                .forEach { values.add(it) }
            if (values.isEmpty()) values.add("Fundamentos")
        }
        return Catalog(JsonObject(root + mapOf(
            "TOPICOS_EDITAL" to JsonObject(updated.mapValues { JsonArray(it.value.map(::JsonPrimitive)) }),
            "DISCIPLINAS_ESTUDO" to JsonArray(updated.keys.sorted().map(::JsonPrimitive))
        )), true)
    }
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

private fun accountCatalog(context: Context, generic: Boolean): JsonObject {
    val legacy = Json.parseToJsonElement(context.assets.open("catalog.json").bufferedReader().use { it.readText() }).jsonObject
    if (!generic) return legacy
    val defaults = Json.parseToJsonElement(context.assets.open("account_defaults.json").bufferedReader().use { it.readText() }).jsonObject
    return JsonObject(legacy + defaults.filterKeys { it in listOf("EXERCICIOS_PRESETADOS", "TOPICOS_EDITAL", "DECKS_ANKI", "FONTES_QUESTOES") } + mapOf(
        "DISCIPLINAS_ESTUDO" to JsonArray(defaults.getValue("TOPICOS_EDITAL").jsonObject.keys.sorted().map(::JsonPrimitive)),
        "ROTA_ESTRATEGICA" to JsonArray(defaults.getValue("TOPICOS_EDITAL").jsonObject.keys.map(::JsonPrimitive)),
        "PESOS_DISCIPLINA" to JsonObject(defaults.getValue("TOPICOS_EDITAL").jsonObject.keys.associateWith { JsonPrimitive(1) })
    ))
}
