package com.matheussantos.solem.data

import android.content.Context
import android.content.SharedPreferences
import com.matheussantos.solem.domain.WalkSession
import kotlinx.serialization.json.Json

/** App-private and account scoped; no location points, cloud writes or backup. */
class WalkSessionStore internal constructor(private val prefs: SharedPreferences) {
    constructor(context: Context):this(context.getSharedPreferences("walk_session_v1",Context.MODE_PRIVATE))
    private val json=Json { ignoreUnknownKeys=true }
    fun read(owner: String): WalkSession? = if(owner.isBlank()) null else runCatching {
        json.decodeFromString<WalkSession>(prefs.getString("session_$owner",null) ?: return null)
            .takeIf {it.owner==owner}
    }.getOrNull()
    fun active(): WalkSession? = read(prefs.getString("active_owner","").orEmpty())?.takeIf {it.pending}
    fun save(value: WalkSession): Boolean {
        if(value.owner.isBlank()) return false
        val editor=prefs.edit().putString("session_${value.owner}",json.encodeToString(value))
        if(value.active) editor.putString("active_owner",value.owner)
        else if(prefs.getString("active_owner",null)==value.owner) editor.remove("active_owner")
        // Commit every distance increment before publishing it to the UI.
        return editor.commit()
    }
}
