package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.data.model.TrainingRecord
import java.time.LocalDate

/** Device-local preferences, never changes the history-derived XP/rank rules. */
data class DashboardPreferences(
    val theme: String = "Escuro", val accent: String = "Glacial", val nickname: String = "",
    val waterMl: Int = 3000, val pushups: Int = 50, val squats: Int = 50,
    val walkKm: Int = 5, val questions: Int = 150, val studyMinutes: Int = 60,
    val mewing: Int = 400, val sleepMinutes: Int = 480,
    val hidden: Set<String> = setOf("sleep"), val motion: Boolean = true,
    val sound: Boolean = true, val showWeek: Boolean = true, val showRecent: Boolean = true
) {
    fun validated(): DashboardPreferences {
        require(theme in listOf("Escuro", "Claro", "Sistema") && accent in listOf("Glacial", "Âmbar", "Rubi"))
        require(nickname.length <= 40)
        require(waterMl in 250..10000 && pushups in 1..10000 && squats in 1..10000 && mewing in 1..10000)
        require(walkKm in 1..100 && questions in 1..5000 && studyMinutes in 1..1440 && sleepMinutes in 1..960)
        require(hidden.all { it in missionIds })
        return copy(nickname = nickname.trim())
    }
    companion object {
        fun defaults(generic: Boolean) = if (generic) DashboardPreferences(
            pushups = 10, squats = 15, walkKm = 1, questions = 20,
            studyMinutes = 30, hidden = setOf("sleep", "mewing")
        ) else DashboardPreferences()
    }
}
val missionIds = setOf("water", "flexao", "agachamento", "walk", "questions", "study", "mewing", "sleep")
data class DailyMission(val id: String, val title: String, val value: Double?, val target: Int,
    val unit: String, val destination: Int, val exercise: String? = null) {
    val complete get() = value != null && value.isFinite() && value >= target
    val fraction get() = ((value?.takeIf {it.isFinite()} ?: 0.0) / target.coerceAtLeast(1)).toFloat().coerceIn(0f, 1f)
}

/** Private health entries are never mixed with shared legacy nutrition records. */
fun dailyMissions(records: List<TrainingRecord>, health: List<HealthEntry>, settings: DashboardPreferences,
    generic: Boolean, healthAvailable: Boolean, day: LocalDate = today()): List<DailyMission> {
    val rows = records.distinctBy { it.id }.filter { it.data.take(10) == day.toString() }
    val workouts = rows.filter { it.isWorkout() }
    val study = rows.filter { it.group == "Estudos" }
    val diary = health.distinctBy { it.id }.filter { it.day == day.toString() }
    fun nonnegative(value:Double)=value.takeIf {it.isFinite() && it>0} ?: 0.0
    fun reps(exercise: String) = workouts.filter { it.exercicio == exercise }.sumOf { it.repeticoes.coerceAtLeast(0).toDouble() }
    val water = diary.filter { it.kind == "water" }.sumOf {
        val volume = it.number("volume_ml"); val count = it.number("quantidade")
        if (volume.isFinite() && count.isFinite() && volume in 50.0..5000.0 && count in 1.0..50.0) volume * count else 0.0
    }
    val sleep = diary.firstOrNull { it.kind == "sleep" }?.number("duracao_min")?.takeIf { it.isFinite() && it in 1.0..960.0 }
    return listOf(
        DailyMission("water", "Hidratação", if (healthAvailable) water else null, settings.waterMl, "ml", 3),
        DailyMission("flexao", "Flexões", reps("Flexão"), settings.pushups, "rep", 1, "Flexão"),
        DailyMission("agachamento", "Agachamentos", reps("Agachamento"), settings.squats, "rep", 1, "Agachamento"),
        DailyMission("walk", "Caminhada ou corrida", workouts.filter { it.exercicio in listOf("Caminhada", "Corrida") }
            .sumOf { it.distanceKm.takeIf { km -> km.isFinite() && km > 0 } ?: 0.0 }, settings.walkKm, "km", 1, "Caminhada"),
        DailyMission("questions", "Questões", study.filter { it.extra("fonte_questoes") != "Anki" }
            .sumOf { nonnegative(it.number("q_certas")) + nonnegative(it.number("q_erradas")) }, settings.questions, "questões", 5),
        DailyMission("study", "Tempo de estudo", study.sumOf { nonnegative(it.studyMinutes()) + nonnegative(it.number("tempo_video")) }, settings.studyMinutes, "min", 5),
        DailyMission("mewing", "Mewing com borracha", reps("Mewing com borracha"), settings.mewing, "rep", 1, "Mewing com borracha"),
        DailyMission("sleep", "Sono registrado", if (healthAvailable) sleep ?: 0.0 else null, settings.sleepMinutes, "min", 3)
    ).filter { it.id !in settings.hidden && (!generic || it.id != "mewing") }
}

data class PromotionCheckpoint(val level: Int, val physicalTier: Int, val topicTiers:Map<String,Int> = emptyMap())
data class JourneyPromotion(val level: Int? = null, val physicalTier: Int? = null,val studyTier:Int?=null,val studyCount:Int=0)
fun journeyPromotion(before: PromotionCheckpoint?, current: PromotionCheckpoint): JourneyPromotion? {
    if (before == null) return null // Initial synchronization is a baseline, not a promotion.
    val level = current.level.takeIf { it > before.level }
    val tier = current.physicalTier.takeIf { it > before.physicalTier }
    val topics=current.topicTiers.filter { (key,value) -> value>=0 && value>(before.topicTiers[key] ?: value) }.values
    return if (level == null && tier == null && topics.isEmpty()) null else JourneyPromotion(level,tier,topics.maxOrNull(),topics.size)
}
