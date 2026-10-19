package com.matheussantos.solem.viewmodel

import com.matheussantos.solem.data.model.PersonalItem
import io.github.jan.supabase.auth.status.RefreshFailureCause
import io.github.jan.supabase.auth.status.SessionStatus
import io.github.jan.supabase.auth.user.UserInfo
import io.github.jan.supabase.auth.user.UserSession
import org.junit.Assert.*
import org.junit.Test

class WorkspaceSessionTest {
    private val connected = WorkspaceState(
        initialized = true, signedIn = true, accountId = "account-a",
        generic = false, sessionGeneration = 7,
        items = listOf(PersonalItem("note-a", "note", "Private note")),
        healthLoaded = true, photoData = mapOf("photo-a" to byteArrayOf(1, 2))
    )

    private fun authenticated(id: String? = "account-a") = SessionStatus.Authenticated(
        UserSession(accessToken = "test-only", refreshToken = "test-only",
            expiresIn = 3600, tokenType = "bearer",
            user = id?.let { UserInfo(aud = "authenticated", id = it) })
    )

    @Test fun switchingAppsDoesNotLogOutOrRecreateAccountScope() {
        // Exact Auth 3.5 Android sequence: onStop -> Initializing;
        // onStart -> loadFromStorage -> Authenticated.
        var state = connected
        repeat(100) {
            state = state.afterAuthStatus(SessionStatus.Initializing)
            assertSame(connected, state)
            state = state.afterAuthStatus(authenticated())
            assertSame(connected, state)
        }
    }

    @Test fun temporaryNetworkFailureThenRecoveryKeepsData() {
        val offline = SessionStatus.RefreshFailure(RefreshFailureCause.NetworkError(java.io.IOException("offline")))
        val state = connected.afterAuthStatus(SessionStatus.Initializing).afterAuthStatus(offline)
        assertSame(connected, state)
        assertSame(connected, state.afterAuthStatus(authenticated()))
    }

    @Test fun actionFailureDuringBackgroundDoesNotClearSession() {
        val state = connected.afterAuthStatus(SessionStatus.Initializing).copy(failed = true, message = "Try again")
        assertTrue(state.signedIn)
        assertEquals(connected.items, state.items)
        assertEquals(7, state.sessionGeneration)
    }

    @Test fun explicitLogoutClearsAllAccountScopedState() {
        val state = connected.afterAuthStatus(SessionStatus.NotAuthenticated(isSignOut = true))
        assertFalse(state.signedIn)
        assertEquals("", state.accountId)
        assertTrue(state.items.isEmpty())
        assertTrue(state.photoData.isEmpty())
        assertFalse(state.healthLoaded)
        assertEquals(8, state.sessionGeneration)
    }

    @Test fun definitiveSessionLossAlsoClearsAccount() {
        assertFalse(connected.afterAuthStatus(SessionStatus.NotAuthenticated()).signedIn)
    }

    @Test fun differentIdentityNeverReceivesPreviousUsersData() {
        val state = connected.afterAuthStatus(authenticated("account-b"))
        assertFalse(state.signedIn)
        assertTrue(state.items.isEmpty())
        assertTrue(state.photoData.isEmpty())
        assertEquals(8, state.sessionGeneration)
    }

    @Test fun authenticatedSessionWithoutIdentityIsNotTrusted() {
        assertFalse(connected.afterAuthStatus(authenticated(null)).signedIn)
    }

    @Test fun lateEventCannotReopenLoggedOutOrUnverifiedAccount() {
        val signedOut = connected.afterAuthStatus(SessionStatus.NotAuthenticated(true))
        assertSame(signedOut, signedOut.afterAuthStatus(authenticated()))
        val pending = WorkspaceState(initialized = true, emailChallenge = "new@example.com")
        assertSame(pending, pending.afterAuthStatus(authenticated("account-b")))
    }
}
