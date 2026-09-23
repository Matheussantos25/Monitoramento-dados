package com.matheussantos.solem.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

@Serializable data class HealthEntry(
    val id: String,
    val day: String,
    @SerialName("logged_at") val loggedAt: String,
    val kind: String,
    val details: JsonObject = JsonObject(emptyMap())
) {
    fun text(key: String): String = (details[key] as? JsonPrimitive)?.content.orEmpty()
    fun number(key: String): Double = text(key).toDoubleOrNull() ?: 0.0
}
