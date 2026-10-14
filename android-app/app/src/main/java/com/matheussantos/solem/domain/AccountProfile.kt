package com.matheussantos.solem.domain

import java.time.Instant

/** Compatibility defaults only, never an authorization/admin role. */
fun genericAccount(email: String?, createdAt: String?, preservedEmail: String, cutoff: String): Boolean {
    if (email.orEmpty().trim().equals(preservedEmail, ignoreCase = true)) return false
    return runCatching { !Instant.parse(createdAt).isBefore(Instant.parse(cutoff)) }.getOrDefault(true)
}

/** Routing only; database RLS is the authority. Never infer ownership from account age. */
fun activityTable(email: String?, preservedEmail: String): String =
    if (!email.isNullOrBlank() && email.trim().equals(preservedEmail, ignoreCase=true)) "treinos" else "solem_activities"

fun fitnessPage(index: Int) = index in setOf(0, 1, 2, 3, 4, 8, 9, 10, 17)
fun fitnessMission(id: String) = id in setOf("water", "flexao", "agachamento", "walk", "sleep")
