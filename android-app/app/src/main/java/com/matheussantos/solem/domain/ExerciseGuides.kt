package com.matheussantos.solem.domain

import kotlinx.serialization.Serializable

@Serializable data class ExerciseGuides(
    val version: Int, val notice: String,
    val motions: Map<String, GuideMotion>, val grips: Map<String, GuideGrip>,
    val guides: Map<String, ExerciseTechnique>
) {
    fun forExercise(name: String) = guides[name] ?: ExerciseTechnique(
        view = "Guia ainda não disponível",
        cues = listOf("Este exercício não tem uma técnica ilustrada definida. Seu registro continua disponível."),
        avoid = "Confirme a execução com um profissional.")
}
@Serializable data class ExerciseTechnique(
    val motion: String = "", val view: String, val cues: List<String>, val avoid: String,
    val labels: List<String> = emptyList(), val grip: String = "", val source: String = ""
)
@Serializable data class GuideMotion(
    val frames: List<GuidePose>,
    val equipment: List<List<List<Float>>> = emptyList(),
    val circles: List<List<Float>> = emptyList()
)
@Serializable data class GuidePose(val head: List<Float>, val lines: List<List<List<Float>>>)
@Serializable data class GuideGrip(
    val lines: List<List<List<Float>>>, val marks: List<List<List<Float>>>,
    val title: String, val caption: String
)
