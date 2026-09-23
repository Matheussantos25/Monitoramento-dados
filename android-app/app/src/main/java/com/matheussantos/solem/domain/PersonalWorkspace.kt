package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.PersonalItem
import java.time.LocalDate

val workspaceKinds = linkedMapOf("Anotações" to "note", "Resumos" to "summary", "Mapas mentais" to "mindmap", "PDFs" to "pdf", "Cronograma" to "plan", "Investimentos" to "investment")
const val MAX_PDF_BYTES = 10 * 1024 * 1024
data class MindNode(val label: String, val parent: Int?, val depth: Int)
fun mindNodes(body: String): List<MindNode> {
    val result = mutableListOf<MindNode>()
    val parents = mutableListOf<Int>()
    body.replace("\r", "").lines().filter { it.isNotBlank() }.forEach { line ->
        val spaces = line.length - line.trimStart(' ').length
        val depth = spaces / 2
        require('\t' !in line && spaces % 2 == 0 && depth <= 5 && line.trim().length <= 160) { "Use 2 espaços por nível, até 5 níveis e 160 caracteres por tópico." }
        require(!(result.isEmpty() && depth != 0) && !(result.isNotEmpty() && depth == 0) && depth <= parents.size) { "Use uma única raiz e não pule níveis." }
        while (parents.size > depth) parents.removeAt(parents.lastIndex)
        result.add(MindNode(line.trim(), parents.lastOrNull(), depth))
        parents.add(result.lastIndex)
    }
    require(result.size in 1..80) { "O mapa deve ter entre 1 e 80 tópicos." }
    return result
}
fun moneyCents(text: String): Long {
    require(Regex("\\d{1,10}([.,]\\d{1,2})?").matches(text.trim())) { "Use valor positivo, sem separador de milhar e com até duas casas decimais." }
    val value = text.trim().replace(',', '.').toBigDecimal().movePointRight(2).longValueExact()
    require(value <= 999999999999L) { "Valor acima do limite suportado." }
    return value
}
fun validatePdf(bytes: ByteArray) {
    require(bytes.size <= MAX_PDF_BYTES && bytes.take(5).toByteArray().decodeToString() == "%PDF-") { "Selecione um PDF válido com até 10 MB." }
}
fun validatePersonalItem(item: PersonalItem) {
    require(item.kind in workspaceKinds.values && item.title.trim().length in 1..160 && item.body.length <= 50000) { "Informe título de até 160 caracteres e conteúdo de até 50 mil caracteres." }
    if (item.kind == "mindmap") mindNodes(item.body)
    if (item.kind in listOf("plan", "investment")) {
        val day = runCatching { LocalDate.parse(item.eventDate) }.getOrNull()
        require(day != null && day.year in 1900..2200) { "Informe uma data válida: AAAA-MM-DD." }
    }
    if (item.kind == "plan") require(item.durationMinutes in 1..1440 && Regex("([01]\\d|2[0-3]):[0-5]\\d").matches(item.eventTime)) { "Informe horário HH:MM e duração entre 1 e 1440 minutos." }
    if (item.kind == "investment") require(item.investedCents in 0..999999999999L && item.valueCents in 0..999999999999L) { "Valor inválido." }
}
