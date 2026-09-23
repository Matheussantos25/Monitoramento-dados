package com.matheussantos.solem.data.repository

import com.matheussantos.solem.data.SupabaseProvider
import com.matheussantos.solem.data.model.TrainingMutation
import com.matheussantos.solem.data.model.TrainingRecord
import io.github.jan.supabase.annotations.SupabaseExperimental
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.realtime.selectAsFlow
import kotlinx.coroutines.flow.Flow

class TrainingRepository {
    private val table = "treinos"
    private val client get() = SupabaseProvider.client

    /** Initial SELECT plus INSERT/UPDATE/DELETE events when treinos is in Realtime replication. */
    @OptIn(SupabaseExperimental::class)
    fun observeAll(): Flow<List<TrainingRecord>> = client.from(table).selectAsFlow(TrainingRecord::id)

    suspend fun insert(value: TrainingMutation) { client.from(table).insert(value) }

    suspend fun insertBatch(values: List<TrainingMutation>) { client.from(table).insert(values) }
    suspend fun fetchAll(): List<TrainingRecord> {
        val rows = mutableListOf<TrainingRecord>()
        var start = 0L
        while (true) {
            val page = client.from(table).select {
                order("id", io.github.jan.supabase.postgrest.query.Order.ASCENDING)
                range(start, start + 499)
            }.decodeList<TrainingRecord>()
            rows.addAll(page)
            if (page.size < 500) return rows
            start += 500
        }
    }

    suspend fun update(id: Long, value: TrainingMutation) {
        val changed = client.from(table).update(value) { select(); filter { eq("id", id) } }.decodeList<TrainingRecord>()
        check(changed.size == 1) { "Registro não encontrado ou sem permissão." }
    }

    suspend fun delete(id: Long) {
        val changed = client.from(table).delete { select(); filter { eq("id", id) } }.decodeList<TrainingRecord>()
        check(changed.size == 1) { "Registro não encontrado ou sem permissão." }
    }
}
