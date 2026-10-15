package com.matheussantos.solem.domain

object EmailAccess {
    const val RESEND_DELAY_MS = 60_000L

    fun normalizeEmail(value: String): String = value.trim()
    fun validEmail(value: String): Boolean {
        val email = normalizeEmail(value)
        return email.length in 3..254 && Regex("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$").matches(email)
    }
    fun validCode(value: String): Boolean = Regex("^[0-9]{6,10}$").matches(value.trim())
    fun resendSeconds(availableAt: Long, now: Long): Int =
        ((availableAt - now).coerceIn(0L, RESEND_DELAY_MS) + 999L).div(1000L).toInt()
}
