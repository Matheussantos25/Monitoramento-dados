package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.*
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class ParityTest {
    private fun resource(name: String) = javaClass.classLoader!!.getResourceAsStream(name)!!.bufferedReader().use { it.readText() }
    private val catalog get() = Catalog(Json.parseToJsonElement(resource("catalog.json")).jsonObject)
    @Test fun importedRowsMatchCanonicalPythonForBothSchemas() {
        val json = Json { encodeDefaults = true }
        Json.parseToJsonElement(resource("import-parity.json")).jsonArray.forEach { element ->
            val fixture = element.jsonObject
            val result = SimulationImport.parse("SOLEM_IMPORT_START\n${fixture["input"]}\nSOLEM_IMPORT_END", catalog.subjects, catalog.topics, "12:00:00")
            assertEquals(fixture["expected"], Json.parseToJsonElement(json.encodeToString(result.rows)))
            assertEquals(7, result.questionCount)
        }
    }
    @Test fun rejectsDuplicateQuestions() {
        val payload = Json.parseToJsonElement(resource("import-parity.json")).jsonArray.first().jsonObject.getValue("input").jsonObject
        val q = payload.getValue("questoes").jsonArray.first()
        val invalid = JsonObject(payload + ("questoes" to JsonArray(listOf(q,q))))
        assertThrows(IllegalArgumentException::class.java) { SimulationImport.parse(invalid.toString(), catalog.subjects, catalog.topics, "12:00:00") }
    }
    @Test fun presetsAndRotationUseWebValues() {
        assertEquals("Bíceps", catalog.group("Barra Fixa (Supinada)"))
        assertEquals(listOf("repeticoes", "isometria_segundos"), catalog.workoutFields("Prancha"))
        assertEquals(listOf("duracao_min", "distancia_km"), catalog.workoutFields("Caminhada"))
        assertEquals(listOf("series", "repeticoes", "descanso_seg"), catalog.workoutFields("Flexão"))
        assertEquals(catalog.route.first(), nextSubject(emptyList(), catalog))
        val row = TrainingRecord(1, "2026-09-06", "12:00:00", "Estudos", catalog.route.last())
        assertEquals(catalog.route.first(), nextSubject(listOf(row), catalog))
        assertTrue(catalog.topics.values.flatten().size > 50)
    }
    @Test fun exactSecondsAndUnknownMetadataSurviveEditing() {
        val extras = buildJsonObject { put("tempo_segundos_exato", 90); put("future_field", "preserve"); put("q_anuladas", 1) }
        val row = TrainingRecord(1, "2026-09-06", "12:00:00", "Estudos", "Disciplina", durationMinutes=2, extras=extras)
        assertEquals(1.5, row.studyMinutes(), 0.0001)
        assertEquals(extras, row.asMutation().copy(data="2026-09-05").extras)
    }
    @Test fun progressIgnoresFutureWeightAndEmptySessionsAndKeepsYesterdayStreak() {
        val now = LocalDate.parse("2026-09-06")
        fun row(id: Long, date: String, group: String, reps: Int=0) = TrainingRecord(id,date,"00:00:00",group,"Registro",repeticoes=reps)
        val records = listOf(row(1,"2026-09-05","Estudos",10), row(2,"2026-09-07","Pernas",10), row(3,"2026-09-06","Métricas"), row(4,"2026-09-06","Peitoral"))
        val progress = calculateProgress(records,now)
        assertEquals(30,progress.xp); assertEquals(1,progress.streak); assertEquals(1,progress.days)
    }
}
