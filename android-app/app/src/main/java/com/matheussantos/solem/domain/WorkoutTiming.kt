package com.matheussantos.solem.domain

fun measuredMillis(accumulated: Long, started: Long, now: Long, running: Boolean): Long =
    accumulated + if (running) (now - started).coerceAtLeast(0) else 0

fun workoutMinutes(seconds: Long): Int {
    require(seconds in 0..86400) { "Tempo fora do intervalo permitido." }
    return ((seconds + 59) / 60).toInt()
}

fun clockText(seconds: Long): String = "%02d:%02d:%02d".format(
    seconds / 3600, seconds / 60 % 60, seconds % 60)
