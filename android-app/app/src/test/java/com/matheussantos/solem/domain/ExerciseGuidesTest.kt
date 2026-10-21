package com.matheussantos.solem.domain

import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class ExerciseGuidesTest {
    private val data = Json.decodeFromString<ExerciseGuides>(javaClass.getResource("/exercise_guides.json")!!.readText())
    @Test fun gripIsExplicitAndDifferent() {
        assertEquals("pronated",data.forExercise("Barra Fixa (Pronada)").grip)
        assertEquals("supinated",data.forExercise("Barra Fixa (Supinada)").grip)
        assertNotEquals(data.grips["pronated"]!!.shapes,data.grips["supinated"]!!.shapes)
        assertNotEquals(data.forExercise("Barra Fixa (Pronada)").motion,data.forExercise("Barra Fixa (Supinada)").motion)
    }
    @Test fun allMotionsResolveAndStaySmall() {
        data.guides.values.filter {it.motion.isNotEmpty()}.forEach { assertNotNull(data.motions[it.motion]) }
        assertTrue(javaClass.getResource("/exercise_guides.json")!!.readBytes().size<350000)
        data.motions.values.forEach { assertTrue(it.frames.size in listOf(1,9)) }
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
    @Test fun continuousPositionsAndEightSecondCycle() {
        val motion=data.motions["pull_pronated"]!!
        assertEquals(motion.frames.first(),motion.sample(0f))
        assertEquals(motion.frames.last(),motion.sample(1f))
        assertEquals(motion.frames[4],motion.sample(.5f))
        assertNotEquals(motion.sample(0f),motion.sample(.06f))
        assertEquals(0f,guidePhase(0),.001f)
        assertEquals(1f,guidePhase(2000),.001f)
        assertEquals(0f,guidePhase(4000),.001f)
        assertEquals(0f,guidePhase(8000),.001f)
    }
}
