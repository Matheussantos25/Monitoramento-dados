package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class EmailAccessTest {
    @Test fun emailIsTrimmedWithoutChangingItsIdentity() {
        assertEquals("Pessoa+treino@exemplo.com", EmailAccess.normalizeEmail(" Pessoa+treino@exemplo.com "))
        assertTrue(EmailAccess.validEmail(" Pessoa+treino@exemplo.com "))
    }
    @Test fun invalidEmailNeverPassesFormValidation() {
        listOf("", "pessoa", "pessoa@", "@exemplo.com", "pessoa @exemplo.com", "pessoa@exemplo",
            "pessoa@@exemplo.com", "x".repeat(250)+"@exemplo.com").forEach { assertFalse(EmailAccess.validEmail(it)) }
    }
    @Test fun codeSupportsConfiguredLengthsWithoutLosingLeadingZeros() {
        assertTrue(EmailAccess.validCode("001234"))
        assertTrue(EmailAccess.validCode(" 00123456 "))
        assertTrue(EmailAccess.validCode("0012345678"))
    }
    @Test fun invalidCodesDoNotGetSubmitted() {
        listOf("", "12345", "12345678901", "123a56", "12 3456", "１２３４５６").forEach {
            assertFalse(EmailAccess.validCode(it))
        }
    }
    @Test fun cooldownCountsDownAndRoundsUp() {
        assertEquals(60, EmailAccess.resendSeconds(61_000,1_000))
        assertEquals(1, EmailAccess.resendSeconds(61_000,60_999))
        assertEquals(0, EmailAccess.resendSeconds(61_000,61_000))
        assertEquals(0, EmailAccess.resendSeconds(61_000,62_000))
    }
    @Test fun deviceClockChangeCannotLeaveAnUnboundedCountdown() {
        assertEquals(60, EmailAccess.resendSeconds(100_000,1_000))
        assertEquals(0, EmailAccess.resendSeconds(0,100_000))
    }
}
