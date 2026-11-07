package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.PersonalItem
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*
import java.util.UUID

const val NOTE_FOLDER_PREFIX = "solem-note-folder-v1\n"
const val NOTE_DOCUMENT_PREFIX = "solem-note-document-v1\n"
const val NOTE_MATERIAL_PREFIX = "solem-note-material-v1\n"
val notesJson = Json { ignoreUnknownKeys = true; encodeDefaults = true }
@Serializable data class NoteBlock(val id: String, val type: String, val text: String = "",
    val ref: String = "", val caption: String = "")
@Serializable data class NoteDocument(val folder: String = "", val blocks: List<NoteBlock> = emptyList())
@Serializable data class NoteEditorEvent(val action: String, val event: String, val title: String,
    val blocks: List<NoteBlock>, val images: Map<String,String>)

fun noteFolder(item: PersonalItem) = item.kind == "note" && item.body.startsWith(NOTE_FOLDER_PREFIX)
fun noteAttachment(item: PersonalItem): JsonObject? = if (item.kind != "note" || !item.body.startsWith(NOTE_MATERIAL_PREFIX)) null
    else runCatching { notesJson.parseToJsonElement(item.body.removePrefix(NOTE_MATERIAL_PREFIX)).jsonObject }.getOrNull()

fun noteDocument(item: PersonalItem?, items: List<PersonalItem>): NoteDocument {
    if (item?.body?.startsWith(NOTE_DOCUMENT_PREFIX) == true)
        return notesJson.decodeFromString<NoteDocument>(item.body.removePrefix(NOTE_DOCUMENT_PREFIX))
    val blocks = mutableListOf(NoteBlock("legacy-text", "text", item?.body.orEmpty()))
    items.forEach { row ->
        val data = noteAttachment(row)
        if (data != null && data["folder"]?.jsonPrimitive?.content == item?.id && !row.archived &&
            data["pending"]?.jsonPrimitive?.booleanOrNull != true) {
            if (data["type"]?.jsonPrimitive?.content == "image")
                blocks += NoteBlock(row.id, "image", ref=row.id, caption=row.title)
            else blocks += NoteBlock(row.id, "text", data["value"]?.jsonPrimitive?.content.orEmpty())
        }
    }
    return NoteDocument(blocks=blocks)
}

fun noteImages(id: String, items: List<PersonalItem>): Map<String,String> = items.mapNotNull { row ->
    val data = noteAttachment(row)
    if (data != null && data["folder"]?.jsonPrimitive?.content == id &&
        data["type"]?.jsonPrimitive?.content == "image" && !row.archived)
        row.id to data["value"]!!.jsonPrimitive.content else null
}.toMap()

fun prepareNote(id: String, folder: String, event: NoteEditorEvent, items: List<PersonalItem>): Pair<PersonalItem,List<PersonalItem>> {
    UUID.fromString(id)
    require(folder.isEmpty() || items.any { it.id == folder && noteFolder(it) && !it.archived }) { "Escolha uma pasta disponível." }
    require(event.blocks.size <= 150) { "Use até 150 blocos por anotação." }
    val existing = noteImages(id, items)
    val assets = mutableMapOf<String,PersonalItem>()
    event.blocks.forEach { block ->
        require(block.type in listOf("text", "image"))
        if (block.type == "image") {
            UUID.fromString(block.ref)
            if (block.ref !in existing) {
                val value = event.images[block.ref].orEmpty()
                val bytes = java.util.Base64.getDecoder().decode(value)
                require(bytes.size in 2..35000 && bytes[0] == 0xff.toByte() && bytes[1] == 0xd8.toByte()) { "Selecione novamente a imagem." }
                val payload = buildJsonObject {
                    put("folder", id); put("type", "image"); put("value", value); put("pending", true)
                }
                assets[block.ref] = PersonalItem(block.ref, "note", block.caption.ifBlank { "Imagem" }.take(160), NOTE_MATERIAL_PREFIX+payload)
            }
        }
    }
    val note = PersonalItem(id, "note", event.title.trim(), NOTE_DOCUMENT_PREFIX+notesJson.encodeToString(NoteDocument(folder, event.blocks)))
    validatePersonalItem(note)
    assets.values.forEach(::validatePersonalItem)
    return note to assets.values.toList()
}
