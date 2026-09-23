package com.matheussantos.solem.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

/** Mirrors public.treinos as used by app.py. No schema is invented here. */
@Serializable
data class TrainingRecord(
    val id: Long,
    val data: String,
    val horario: String,
    @SerialName("grupo_muscular") val group: String,
    val exercicio: String,
    val series: Int = 0,
    val repeticoes: Int = 0,
    @SerialName("carga_kg") val loadKg: Double = 0.0,
    @SerialName("descanso_seg") val restSeconds: Int = 0,
    @SerialName("duracao_min") val durationMinutes: Int = 0,
    @SerialName("distancia_km") val distanceKm: Double = 0.0,
    @SerialName("alimentacao_saudavel") val healthyFood: String = "",
    @SerialName("alimentacao_besteirol") val junkFood: String = "",
    @SerialName("peso_corporal") val bodyWeight: Double = 0.0,
    @SerialName("dados_extras") val extras: JsonObject = JsonObject(emptyMap())
)

@Serializable
data class TrainingMutation(
    val data: String,
    val horario: String,
    @SerialName("grupo_muscular") val group: String,
    val exercicio: String,
    val series: Int = 0,
    val repeticoes: Int = 0,
    @SerialName("carga_kg") val loadKg: Double = 0.0,
    @SerialName("descanso_seg") val restSeconds: Int = 0,
    @SerialName("duracao_min") val durationMinutes: Int = 0,
    @SerialName("distancia_km") val distanceKm: Double = 0.0,
    @SerialName("alimentacao_saudavel") val healthyFood: String = "",
    @SerialName("alimentacao_besteirol") val junkFood: String = "",
    @SerialName("peso_corporal") val bodyWeight: Double = 0.0,
    @SerialName("dados_extras") val extras: JsonObject = JsonObject(emptyMap())
)

fun TrainingRecord.asMutation() = TrainingMutation(data, horario, group, exercicio, series, repeticoes, loadKg, restSeconds, durationMinutes, distanceKm, healthyFood, junkFood, bodyWeight, extras)
