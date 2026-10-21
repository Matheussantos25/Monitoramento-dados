package com.matheussantos.solem.domain

import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class ExerciseGuidesTest {
    private val data = Json.decodeFromString<ExerciseGuides>(javaClass.getResource("/exercise_guides.json")!!.readText())
    @Test fun gripIsExplicitAndDifferent() {
        assertEquals("pronated",data.forExercise("Barra Fixa (Pronada)").grip)
        assertEquals("supinated",data.forExercise("Barra Fixa (Supinada)").grip)
        assertNotEquals(data.grips["pronated"]!!.marks,data.grips["supinated"]!!.marks)
    }
    @Test fun allMotionsResolveAndStaySmall() {
        data.guides.values.filter {it.motion.isNotEmpty()}.forEach { assertNotNull(data.motions[it.motion]) }
        assertTrue(javaClass.getResource("/exercise_guides.json")!!.readBytes().size<25000)
        data.motions.values.forEach { assertTrue(it.frames.size in 1..2) }
    }
    @Test fun unknownAndAmbiguousExercisesNeverGuessTechnique() {
        assertEquals("",data.forExercise("Meu exercício novo").motion)
        assertEquals("legraise",data.forExercise("Abdominal Levantada").motion)
        assertEquals("standingrow",data.forExercise("Remada em Pé na Polia").motion)
        assertEquals("",data.forExercise("Mewing com borracha").motion)
    }
    @Test fun staticHoldsDoNotGetRepetitionAnimation() {
        listOf("Prancha","L-Sit","Handstand (Parada de Mãos)").forEach {
            assertEquals(1,data.motions[data.forExercise(it).motion]!!.frames.size)
        }
    }
}
