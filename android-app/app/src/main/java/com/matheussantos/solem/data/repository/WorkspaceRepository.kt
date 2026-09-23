package com.matheussantos.solem.data.repository

import com.matheussantos.solem.BuildConfig
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.domain.*
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.auth.Auth
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Order
import io.github.jan.supabase.storage.Storage
import io.github.jan.supabase.storage.storage
import io.ktor.http.ContentType
import kotlinx.serialization.json.*

class WorkspaceRepository {
    // Separate from the legacy training client: never changes its anonymous session.
    val client = createSupabaseClient(BuildConfig.SUPABASE_URL, BuildConfig.SUPABASE_PUBLISHABLE_KEY) {
        install(Auth)
        install(Postgrest)
        install(Storage)
    }
    suspend fun list(): List<PersonalItem> {
        check(client.auth.currentUserOrNull() != null) { "Entre novamente para abrir seu espaço privado." }
        val rows = mutableListOf<PersonalItem>()
        while (true) {
            val page = client.from("solem_items").select {
                order("created_at", Order.ASCENDING); order("id", Order.ASCENDING)
                range(rows.size.toLong(), rows.size.toLong() + 499)
            }.decodeList<PersonalItem>()
            rows.addAll(page)
            if (page.size < 500) return rows
        }
    }
    suspend fun save(item: PersonalItem, old: PersonalItem?): PersonalItem {
        validatePersonalItem(item)
        val payload = buildJsonObject {
            if (old == null) put("id", item.id)
            put("kind",item.kind); put("title",item.title.trim()); put("body",item.body)
            put("event_date",item.eventDate?.let { JsonPrimitive(it) } ?: JsonNull)
            put("event_time",item.eventTime); put("duration_minutes",item.durationMinutes); put("done",item.done)
            put("invested_cents",item.investedCents); put("value_cents",item.valueCents)
        }
        val changed = if (old == null) client.from("solem_items").insert(payload) { select() }.decodeList<PersonalItem>()
        else client.from("solem_items").update(payload) { select(); filter { eq("id",old.id); eq("revision",old.revision) } }.decodeList<PersonalItem>()
        require(changed.size == 1) { "Registro alterado em outro dispositivo. Atualize antes de editar novamente." }
        return changed.single()
    }
    suspend fun archive(item: PersonalItem, archived: Boolean) {
        val changed = client.from("solem_items").update(buildJsonObject { put("archived",archived) }) { select(); filter { eq("id",item.id); eq("revision",item.revision) } }.decodeList<PersonalItem>()
        require(changed.size == 1) { "Registro alterado em outro dispositivo. Atualize a lista." }
    }
    suspend fun upload(item: PersonalItem, bytes: ByteArray) {
        validatePdf(bytes)
        client.storage.from("solem-documents").upload(requireNotNull(item.filePath), bytes) { upsert = false; contentType = ContentType.Application.Pdf }
    }
    suspend fun download(item: PersonalItem): ByteArray = client.storage.from("solem-documents").downloadAuthenticated(requireNotNull(item.filePath)).also(::validatePdf)
}
