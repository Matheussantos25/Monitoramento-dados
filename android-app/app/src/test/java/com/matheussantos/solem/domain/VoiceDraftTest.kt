package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class VoiceDraftTest {
    private val foods:List<MealReference> = mealJson.decodeFromString(javaClass.getResource("/nutrition_catalog.json")!!.readText())
    @Test fun cumulativeFullMeal() {
        val text="Almoço arroz 170, feijão 323, ovo cozido 371, alface 386, purê 457, carne 491, peso acumulado"
        val draft=parseMealVoice(text,foods)
        assertEquals(listOf(170.0,153.0,48.0,15.0,71.0,34.0),draft.items.map {it.grams})
        assertTrue(draft.cumulative);assertEquals("Almoço",draft.mealType)
        assertEquals(491.0,draft.items.sumOf {it.grams},0.001)
        assertEquals(listOf(170.0,153.0,48.0),parseMealVoice("Acumulado arroz cento e setenta, feijão trezentos e vinte e três, ovo cozido trezentos e setenta e um",foods).items.map {it.grams})
        assertEquals(60.0,parseMealVoice("arroz 70,5 gramas, feijão 130,5 gramas",foods).items[1].grams,0.001)
    }
    @Test fun explicitIndividualAndRepeatedIngredient() {
        val draft=parseMealVoice("Jantar arroz 170, feijão 153, individual",foods)
        assertFalse(draft.cumulative);assertEquals(listOf(170.0,153.0),draft.items.map {it.grams})
        assertEquals(listOf(70.0,50.0),parseMealVoice("arroz 70, arroz 120",foods).items.map {it.grams})
    }
    @Test fun noSilentPartialMealOrGuessedUnits() {
        listOf("arroz 170, feijão 160, acumulado","arroz 170, feijão 170","arroz 170, comida desconhecida 200","arroz 170, frango", "arroz 170, individual e acumulado","arroz 2 kg","almoço jantar arroz 170","arroz -10","arroz 170, feijão 4000","arroz 170, feijão 323, ontem","arroz 170, prato 60","arroz 170 200").forEach {text->
            assertTrue(text,runCatching {parseMealVoice(text,foods)}.isFailure)
        }
    }
    @Test fun weightAndSleep() {
        assertEquals(67.5,parseWeightVoice("Peso sessenta e sete vírgula cinco quilos").kg!!,0.001)
        assertEquals(67.5,parseWeightVoice("67,5").kg!!,0.001)
        val sleep=parseSleepVoice("Dormi às três e acordei às treze e meia, na mesma data")
        assertEquals("03:00",sleep.bed);assertEquals("13:30",sleep.wake);assertEquals("same",sleep.mode)
        assertEquals("01:15",parseSleepVoice("Dormi uma e quinze e acordei oito e quarenta e cinco").bed)
        assertEquals("23:30",parseSleepVoice("Dormi às vinte e três e trinta e acordei às sete, na noite anterior").bed)
        listOf("Dormi às 25 e acordei às 7","Dormi às 3 e acordei 13:70","Dormi ontem às 3 e acordei às 8").forEach {assertTrue(runCatching {parseSleepVoice(it)}.isFailure)}
        listOf("peso 700 kg","peso 67 libras","peso 67 e 68","-67").forEach {assertTrue(runCatching {parseWeightVoice(it)}.isFailure)}
    }
    @Test fun exerciseSeriesAreMultipliedAndCardioUnitsPreserved() {
        val exercises=listOf("Agachamento","Flexão","Caminhada","Prancha")
        val squat=parseWorkoutVoice("Agachamento, três séries de vinte, descanso de um minuto",exercises,"Flexão")
        assertEquals("Agachamento",squat.exercise)
        assertEquals(mapOf("series" to 3.0,"repeticoes" to 60.0,"descanso_seg" to 60.0),squat.values)
        assertEquals("Agachamento",parseWorkoutVoice("20 agachamentos",exercises,"Flexão").exercise)
        assertEquals(mapOf("duracao_min" to 30.0,"distancia_km" to 2.5),parseWorkoutVoice("Caminhada, 30 minutos, 2 vírgula 5 quilômetros",exercises,"Flexão").values)
        assertEquals(mapOf("repeticoes" to 2.0,"isometria_segundos" to 30.0),parseWorkoutVoice("Prancha, 2 repetições, 30 segundos",exercises,"Flexão").values)
        listOf("Agachamento 20 e Flexão 30","agachamento 3 séries de 20 e 40 repetições","Caminhada 2 milhas").forEach {assertTrue(runCatching {parseWorkoutVoice(it,exercises,"Flexão")}.isFailure)}
    }
}
