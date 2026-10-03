package com.matheussantos.solem.domain

import java.time.Instant

/** Compatibility defaults only, never an authorization/admin role. */
fun genericAccount(email: String?, createdAt: String?, preservedEmail: String, cutoff: String): Boolean {
    if (email.orEmpty().trim().equals(preservedEmail, ignoreCase = true)) return false
    return runCatching { !Instant.parse(createdAt).isBefore(Instant.parse(cutoff)) }.getOrDefault(true)
}
