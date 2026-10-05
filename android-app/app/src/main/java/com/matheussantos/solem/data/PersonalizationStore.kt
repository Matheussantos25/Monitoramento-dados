package com.matheussantos.solem.data

import android.content.Context
import com.matheussantos.solem.domain.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class PersonalizationStore(context: Context, accountId: String, generic: Boolean) {
    // UUID account id isolates settings on shared devices. Guest has no health data.
    private val prefs = context.getSharedPreferences("solem_style_${accountId.ifBlank { "guest" }}", Context.MODE_PRIVATE)
    private val defaults = DashboardPreferences.defaults(generic)
    private fun read() = runCatching {
        defaults.copy(theme = prefs.getString("theme", defaults.theme)!!, accent = prefs.getString("accent", defaults.accent)!!,
            nickname = prefs.getString("nickname", "")!!, waterMl = prefs.getInt("water", defaults.waterMl),
            pushups = prefs.getInt("pushups", defaults.pushups), squats = prefs.getInt("squats", defaults.squats),
            walkKm = prefs.getInt("walk", defaults.walkKm), questions = prefs.getInt("questions", defaults.questions),
            studyMinutes = prefs.getInt("study", defaults.studyMinutes), mewing = prefs.getInt("mewing", defaults.mewing),
            sleepMinutes = prefs.getInt("sleep", defaults.sleepMinutes), hidden = prefs.getStringSet("hidden", defaults.hidden)!!.toSet(),
            motion = prefs.getBoolean("motion", true), sound = prefs.getBoolean("sound", true),
            showWeek = prefs.getBoolean("week", true), showRecent = prefs.getBoolean("recent", true)).validated()
    }.getOrDefault(defaults)
    private val mutableState = MutableStateFlow(read())
    val state = mutableState.asStateFlow()
    fun save(value: DashboardPreferences) {
        val checked = value.validated()
        prefs.edit().putString("theme", checked.theme).putString("accent", checked.accent).putString("nickname", checked.nickname)
            .putInt("water", checked.waterMl).putInt("pushups", checked.pushups).putInt("squats", checked.squats)
            .putInt("walk", checked.walkKm).putInt("questions", checked.questions).putInt("study", checked.studyMinutes)
            .putInt("mewing", checked.mewing).putInt("sleep", checked.sleepMinutes).putStringSet("hidden", checked.hidden)
            .putBoolean("motion", checked.motion).putBoolean("sound", checked.sound)
            .putBoolean("week", checked.showWeek).putBoolean("recent", checked.showRecent).apply()
        mutableState.value = checked
    }
    fun reset() = save(defaults)
    fun checkpoint(): PromotionCheckpoint? = if (!prefs.contains("level")) null
        else PromotionCheckpoint(prefs.getInt("level", 1), prefs.getInt("tier", 0),
            prefs.all.filter {it.key.startsWith("topic:") && it.value is Int}.mapKeys {it.key.removePrefix("topic:")}.mapValues {it.value as Int})
    fun recordCheckpoint(value: PromotionCheckpoint) {
        val old = checkpoint()
        val edit=prefs.edit().putInt("level", maxOf(value.level, old?.level ?: 1))
            .putInt("tier", maxOf(value.physicalTier, old?.physicalTier ?: 0))
        value.topicTiers.forEach {(key,tier) -> edit.putInt("topic:$key",maxOf(tier,old?.topicTiers?.get(key) ?: -1))}
        edit.apply()
    }
}
