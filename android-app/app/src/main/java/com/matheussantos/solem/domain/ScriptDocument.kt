package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.PersonalItem
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString

const val SCRIPT_PREFIX="SOLEM_SCRIPT_V1\n"
@Serializable data class ScriptDocument(val type:String="idea",val text:String="",val description:String="",val tags:String="")
fun scriptDocument(item:PersonalItem):ScriptDocument? {
    if(item.kind!="note" || !item.body.startsWith(SCRIPT_PREFIX)) return null
    return runCatching {mealJson.decodeFromString<ScriptDocument>(item.body.removePrefix(SCRIPT_PREFIX))}
        .getOrNull()?.takeIf {it.type in listOf("idea","script")}
}
fun scriptBody(document:ScriptDocument):String {
    require(document.type in listOf("idea","script") && document.text.length<=40000 && document.description.length<=3000 && document.tags.length<=500) {"Confira os limites dos campos."}
    return (SCRIPT_PREFIX+mealJson.encodeToString(document)).also {require(it.length<=50000) {"Texto muito longo para salvar."}}
}
