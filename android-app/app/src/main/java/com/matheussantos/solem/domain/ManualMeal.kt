package com.matheussantos.solem.domain

import kotlinx.serialization.json.*

fun manualMealDetails(kind: String, healthy: List<String>, occasional: List<String>, skipped: Boolean): JsonObject {
    val good = if (skipped) emptyList() else healthy.map { it.trim() }.filter { it.isNotEmpty() }
    val other = if (skipped) emptyList() else occasional.map { it.trim() }.filter { it.isNotEmpty() }
    require(skipped || good.isNotEmpty() || other.isNotEmpty()) { "Selecione um alimento ou marque Sem refeição." }
    return buildJsonObject {
        put("tipo_refeicao", kind)
        put("sem_refeicao", skipped)
        put("saudaveis", buildJsonArray { good.forEach { add(JsonPrimitive(it)) } })
        put("ocasionais", buildJsonArray { other.forEach { add(JsonPrimitive(it)) } })
    }
}
