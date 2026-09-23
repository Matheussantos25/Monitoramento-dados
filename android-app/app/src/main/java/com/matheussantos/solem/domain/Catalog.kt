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
    fun group(exercise: String) = groups.entries.firstOrNull { exercise in it.value }?.key ?: "Outro"
}
