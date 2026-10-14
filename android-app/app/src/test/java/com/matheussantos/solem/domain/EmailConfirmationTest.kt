package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test
import kotlinx.coroutines.runBlocking

class EmailConfirmationTest {
    private val base = EmailConfirmation.REDIRECT_URL

    @Test fun acceptsExactPkceCallback() {
        assertEquals(EmailConfirmation.Result.Code("test-code"), EmailConfirmation.parse("$base?code=test-code"))
    }
    @Test fun rejectsOtherDestinations() {
        listOf("https://auth/callback?code=x", "com.other://auth/callback?code=x",
            "com.matheussantos.solem://other/callback?code=x", "$base/extra?code=x",
            "com.matheussantos.solem://user@auth/callback?code=x",
            "com.matheussantos.solem://auth:80/callback?code=x").forEach {
            assertEquals(EmailConfirmation.Result.Ignore, EmailConfirmation.parse(it))
        }
    }
    @Test fun rejectsErrorsEmptyAndDuplicateCodes() {
        listOf(base, "$base?code=", "$base?code=%20", "$base?code=a&code=b",
            "$base?code=x&error=access_denied", "$base?error_code=otp_expired",
            "$base?code=%ZZ").forEach {
            assertEquals(EmailConfirmation.Result.Invalid, EmailConfirmation.parse(it))
        }
    }
    @Test fun rejectsImplicitAndInjectedTokens() {
        listOf("$base#access_token=x&refresh_token=y", "$base?code=x#access_token=x",
            "$base?code=x&access_token=y", "$base?code=x&refresh_token=y").forEach {
            assertEquals(EmailConfirmation.Result.Invalid, EmailConfirmation.parse(it))
        }
    }
    @Test fun onlyAcceptsThePendingSignupIdentity() {
        assertTrue(EmailConfirmation.matchesPendingAccount(" New@example.com ", "new@example.com"))
        assertFalse(EmailConfirmation.matchesPendingAccount("new@example.com", "owner@example.com"))
        assertFalse(EmailConfirmation.matchesPendingAccount(null, "new@example.com"))
        assertFalse(EmailConfirmation.matchesPendingAccount("new@example.com", null))
        assertFalse(EmailConfirmation.matchesPendingAccount("", ""))
    }

    @Test fun importsOnlyAfterServerVerification() = runBlocking {
        val events = mutableListOf<String>()
        EmailConfirmation.complete("one-time-code", "new@example.com",
            exchange={ events.add("exchange"); "unverified" },
            verify={ events.add("verify"); "verified" to "new@example.com" },
            adopt={ events.add("import:$it") })
        assertEquals(listOf("exchange", "verify", "import:verified"), events)
    }

    @Test fun otherAccountNeverGetsImported() = runBlocking {
        var imported = false
        val result = runCatching {
            EmailConfirmation.complete("code", "new@example.com",
                exchange={ "session" }, verify={ it to "owner@example.com" }, adopt={ imported=true })
        }
        assertTrue(result.isFailure)
        assertFalse(imported)
    }

    @Test fun expiredCodeNeverGetsVerifiedOrImported() = runBlocking {
        val events = mutableListOf<String>()
        val result = runCatching {
            EmailConfirmation.complete<String>("expired", "new@example.com",
                exchange={ throw IllegalStateException("expired") },
                verify={ events.add("verify"); it to "new@example.com" }, adopt={ events.add("import") })
        }
        assertTrue(result.isFailure)
        assertTrue(events.isEmpty())
    }

    @Test fun failedUserVerificationNeverImportsSession() = runBlocking {
        var imported = false
        val result = runCatching {
            EmailConfirmation.complete("code", "new@example.com",
                exchange={ "session" }, verify={ throw IllegalStateException("offline") }, adopt={ imported=true })
        }
        assertTrue(result.isFailure)
        assertFalse(imported)
    }
}
