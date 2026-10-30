package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import java.net.URI
import java.time.LocalDate

fun validMotivationLink(value:String):Boolean = runCatching {
    val uri=URI(value)
    uri.scheme == "https" && uri.host in setOf("youtube.com","www.youtube.com","youtu.be","music.youtube.com","open.spotify.com","soundcloud.com","www.soundcloud.com") &&
        uri.userInfo==null && uri.port in listOf(-1,443) && value.length<=500 && value.none {it.code<32}
}.getOrDefault(false)

data class RhythmDay(val date:LocalDate,val sessions:Int,val reps:Int,val km:Double)
fun workoutRhythm(rows:List<TrainingRecord>,day:LocalDate):List<RhythmDay> = (6 downTo 0).map {offset ->
    val date=day.minusDays(offset.toLong())
    val workouts=rows.distinctBy {it.id}.filter {it.data.take(10)==date.toString() && it.isWorkout() &&
        (it.repeticoes>0 || it.durationMinutes>0 || it.distanceKm>0 || it.number("isometria_segundos")>0)}
    RhythmDay(date,workouts.size,workouts.sumOf {it.repeticoes.coerceAtLeast(0)},
        workouts.sumOf {it.distanceKm.takeIf {n -> n.isFinite() && n>0} ?: 0.0})
}
