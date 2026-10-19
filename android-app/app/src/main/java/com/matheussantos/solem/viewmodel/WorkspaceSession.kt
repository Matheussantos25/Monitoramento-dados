package com.matheussantos.solem.viewmodel

import io.github.jan.supabase.auth.status.SessionStatus

/**
 * Auth 3.5 emits Initializing when Android backgrounds the process. This is not
 * a logout: currentUserOrNull() is also null until the saved session is resumed.
 * Keep the account-scoped UI through that transition and recoverable refresh
 * failures; only a definitive logout or a different identity clears its data.
 */
internal fun WorkspaceState.afterAuthStatus(status: SessionStatus): WorkspaceState {
    if (!signedIn) return this // Login/OTP must still verify the requested identity.
    val ended = when (status) {
        is SessionStatus.NotAuthenticated -> true
        is SessionStatus.Authenticated -> status.session.user?.id != accountId
        SessionStatus.Initializing, is SessionStatus.RefreshFailure -> false
    }
    return if (ended) WorkspaceState(
        initialized = true,
        sessionGeneration = sessionGeneration + 1,
        message = "Sessão encerrada. Entre novamente."
    ) else this
}
