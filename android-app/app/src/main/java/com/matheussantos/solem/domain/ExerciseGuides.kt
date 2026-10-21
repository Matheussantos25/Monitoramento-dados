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
    val shapes: List<GuideShape>, val frames: List<List<List<Float>>>,
    val static: List<GuideVector> = emptyList(), val direction: String = "",
    val landmarks: List<String> = emptyList()
) {
    fun sample(position: Float): List<List<Float>> {
        val p = position.coerceIn(0f,1f)*(frames.size-1)
        val index = p.toInt(); val t = p-index
        val a = frames[index]; val b = frames[minOf(index+1,frames.lastIndex)]
        return a.mapIndexed { j, coords -> coords.mapIndexed { k,v -> v+(b[j][k]-v)*t } }
    }
}
@Serializable data class GuideShape(
    val kind: String, val commands: String = "", val fill: String = "",
    val stroke: String = "", val width: Float = 0f
)
@Serializable data class GuideVector(val shape: GuideShape, val coords: List<Float>)
@Serializable data class GuideGrip(
    val shapes: List<GuideVector>, val title: String, val caption: String, val instruction: String
)

fun guidePhase(elapsedMillis: Long): Float =
    ((1-kotlin.math.cos(2*Math.PI*elapsedMillis.coerceIn(0,8000)/4000.0))/2).toFloat()
