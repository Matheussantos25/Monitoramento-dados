package com.matheussantos.solem.data.repository

import com.matheussantos.solem.data.model.HealthEntry
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Order
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

class HealthRepository(private val client: SupabaseClient) {
    suspend fun list(): List<HealthEntry> {
        check(client.auth.currentUserOrNull() != null) { "Entre novamente para abrir o diário privado." }
        val rows = mutableListOf<HealthEntry>()
        while (true) {
            val page = client.from("solem_health_entries").select {
                order("day", Order.DESCENDING); order("logged_at", Order.DESCENDING)
                range(rows.size.toLong(), rows.size.toLong() + 499)
            }.decodeList<HealthEntry>()
            rows.addAll(page)
            if (page.size < 500) return rows
        }
    }

    suspend fun save(day: String, time: String, kind: String, details: JsonObject, id: String? = null) {
        require(kind in listOf("meal", "water", "weight", "sleep"))
        val value = buildJsonObject {
            put("day", day); put("logged_at", time); put("kind", kind); put("details", details)
        }
        if (id == null) client.from("solem_health_entries").insert(value)
        else client.from("solem_health_entries").update(value) { filter { eq("id", id) } }
    }

    suspend fun delete(id: String) {
        client.from("solem_health_entries").delete { filter { eq("id", id) } }
    }
}
