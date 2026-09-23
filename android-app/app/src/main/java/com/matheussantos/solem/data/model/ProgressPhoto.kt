package com.matheussantos.solem.data.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable data class ProgressPhoto(
    val id: String,
    val day: String,
    val kind: String,
    @SerialName("file_path") val filePath: String
)
