package com.matheussantos.solem.data.model

import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName

@Serializable data class PersonalItem(
    val id: String,
    val kind: String,
    val title: String,
    val body: String = "",
    @SerialName("event_date") val eventDate: String? = null,
    @SerialName("event_time") val eventTime: String = "",
    @SerialName("duration_minutes") val durationMinutes: Int = 0,
    val done: Boolean = false,
    @SerialName("invested_cents") val investedCents: Long = 0,
    @SerialName("value_cents") val valueCents: Long = 0,
    @SerialName("file_path") val filePath: String? = null,
    val archived: Boolean = false,
    val revision: Int = 1
)
