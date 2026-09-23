package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingMutation
import kotlinx.serialization.json.*
import java.time.LocalDate
import java.time.format.DateTimeFormatter

data class ImportResult(val id: String, val rows: List<TrainingMutation>, val questionCount: Int, val warnings: List<String>)
object SimulationImport {
    private fun JsonObject.text(key: String) = (this[key] as? JsonPrimitive)?.contentOrNull.orEmpty()
    fun parse(input: String, subjects: List<String>, topics: Map<String,List<String>>, time: String): ImportResult {
        val segment = if ("SOLEM_IMPORT_START" in input && "SOLEM_IMPORT_END" in input)
            input.substringAfter("SOLEM_IMPORT_START").substringBefore("SOLEM_IMPORT_END") else input
        val begin = segment.indexOf('{'); val end = segment.lastIndexOf('}')
        require(begin >= 0 && end > begin) { "Cole o JSON completo do simulado." }
        val root = Json.parseToJsonElement(segment.substring(begin, end+1)).jsonObject
        val schema = root.text("schema")
        require(schema in listOf("solem_simulado_v1", "solem_simulado_ce_v1")) { "Schema de simulado não reconhecido." }
        val id = root.text("simulado_id").trim()
        require(id.isNotBlank() && id.length <= 100) { "Informe simulado_id com até 100 caracteres." }
        val date = runCatching { LocalDate.parse(root.text("data")) }.getOrElse {
            LocalDate.parse(root.text("data"), DateTimeFormatter.ofPattern("dd/MM/uuuu").withResolverStyle(java.time.format.ResolverStyle.STRICT))
        }.toString()
        val questions = root["questoes"]?.jsonArray ?: error("Questões ausentes.")
        require(questions.size in 1..500) { "Importe entre 1 e 500 questões." }
        val numbers = mutableSetOf<Int>()
        val warnings = mutableListOf<String>()
        if (questions.size != 70) warnings += "O arquivo contém ${questions.size} questões; a importação parcial é permitida."
        data class Group(val subject: String, val topic: String, val details: MutableList<JsonObject> = mutableListOf(), var correct: Int = 0, var wrong: Int = 0, var cancelled: Int = 0, var seconds: Int = 0, var exact: Boolean = true, var minutes: Int = 0)
        val groups = linkedMapOf<Pair<String,String>, Group>()
        questions.forEach { element ->
            val q = element.jsonObject
            val n = q.text("numero").toIntOrNull() ?: error("Número de questão inválido.")
            require(n > 0 && numbers.add(n)) { "Número repetido ou inválido: $n." }
            val subject = q.text("disciplina").trim()
            require(subject in subjects) { "Questão $n: disciplina não reconhecida." }
            val topic = q.text("topico_edital").trim()
            require(topic.isNotBlank() && topic.length <= 500 && topic.lowercase() !in listOf("geral", "simulado / visão geral", "simulado/visão geral", "diversos")) { "Questão $n: informe tópico específico." }
            if (topic !in topics[subject].orEmpty()) warnings += "Tópico preservado fora da lista do edital: $topic"
            val result = when(q.text("resultado").trim().lowercase()) {
                "correta", "correto", "certo", "acerto" -> "correta"
                "errada", "errado", "erro" -> "errada"
                "anulada", "anulado" -> "anulada"
                else -> error("Questão $n: resultado inválido.")
            }
            val timeValue = q["tempo_segundos"] as? JsonPrimitive ?: error("Questão $n: tempo ausente.")
            val seconds = if (timeValue.isString) {
                val parts = timeValue.content.split(":").map { it.trim().toIntOrNull() ?: error("Tempo inválido.") }
                require(parts.size in 2..3 && parts.all { it >= 0 } && parts.last() <= 59 && (parts.size == 2 || parts[1] <= 59)) { "Use mm:ss ou hh:mm:ss." }
                parts.fold(0L) { value, p -> Math.addExact(Math.multiplyExact(value, 60L), p.toLong()) }.also { require(it <= 86400) }.toInt()
            } else {
                val numeric = timeValue.doubleOrNull ?: error("Tempo inválido.")
                require(numeric.isFinite()) { "Tempo inválido." }
                Math.rint(numeric).also { require(it in 0.0..86400.0) { "Tempo deve ficar entre 0 e 24 horas." } }.toInt()
            }
            val informed = q["tempo_informado"] != JsonPrimitive(false)
            if (!informed) warnings += "Questão $n sem tempo medido."
            val confidence = q.text("confianca").ifBlank { null }?.let {
                it.toIntOrNull()?.takeIf { value -> value in 1..3 } ?: error("Questão $n: confiança deve ser 1, 2 ou 3.")
            }
            val g = groups.getOrPut(subject to topic) { Group(subject, topic) }
            if (result == "correta") g.correct++ else if (result == "errada") g.wrong++ else g.cancelled++
            g.seconds += seconds; g.exact = g.exact && informed
            g.details += buildJsonObject {
                put("numero", n); put("resultado", result); put("tempo_segundos", seconds); put("tempo_informado", informed)
                put("confianca", confidence?.let { JsonPrimitive(it) } ?: JsonNull)
                put("resposta_usuario", q.text("resposta_usuario").trim().uppercase())
                put("gabarito", q.text("gabarito").trim().uppercase())
                put("marcacao", q.text("marcacao").trim())
                put("tipo_erro", q["tipo_erro"] ?: JsonNull)
            }
        }
        val totalMinutes = Math.rint(groups.values.sumOf { it.seconds }.toDouble()/60).toInt()
        groups.values.forEach { it.minutes = it.seconds / 60 }
        groups.values.sortedByDescending { it.seconds % 60 }.take(totalMinutes-groups.values.sumOf { it.minutes }).forEach { it.minutes++ }
        val importId = "solem:" + id.lowercase().replace("ß", "ss").replace("ς", "σ")
        val rows = groups.values.map { g -> TrainingMutation(date, time, "Estudos", g.subject,
            repeticoes = g.correct+g.wrong, durationMinutes = g.minutes, extras = buildJsonObject {
                put("topico_edital", g.topic); put("q_certas", g.correct); put("q_erradas", g.wrong); put("q_anuladas", g.cancelled); put("tempo_video", 0)
                put("fonte_questoes", if (schema == "solem_simulado_ce_v1") "IA (FGV adaptado C/E)" else "IA (Estilo FGV)")
                put("origem_importacao", "simulado_json"); put("simulado_id", id); put("importacao_id", importId)
                put("tempo_segundos_exato", g.seconds); put("tempo_estimado", !g.exact)
                put("questoes_numeros", JsonArray(g.details.map { it["numero"]!! }.sortedBy { it.jsonPrimitive.int }))
                put("detalhes_questoes", JsonArray(g.details))
            })
        }
        return ImportResult(importId, rows, questions.size, warnings.distinct())
    }
}
