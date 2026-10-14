package com.matheussantos.solem.domain

import java.net.URI
import java.net.URLDecoder

object EmailConfirmation {
    const val SCHEME = "com.matheussantos.solem"
    const val HOST = "auth"
    const val REDIRECT_URL = "$SCHEME://$HOST/callback"

    sealed interface Result {
        data class Code(val value: String) : Result
        data object Invalid : Result
        data object Ignore : Result
    }

    /** Only accept our exact PKCE callback; never import tokens supplied in a link. */
    fun parse(url: String): Result = try {
        val uri = URI(url)
        if (uri.scheme != SCHEME || uri.host != HOST || uri.path != "/callback" ||
            uri.port != -1 || uri.userInfo != null) Result.Ignore
        else if (uri.rawFragment != null) Result.Invalid
        else {
            val params = uri.rawQuery.orEmpty().split('&').filter { it.isNotEmpty() }.map {
                val pair = it.split('=', limit = 2)
                URLDecoder.decode(pair[0], "UTF-8") to URLDecoder.decode(pair.getOrElse(1) { "" }, "UTF-8")
            }
            val codes = params.filter { it.first == "code" }
            if (params.any { it.first in setOf("error", "error_code", "access_token", "refresh_token") } ||
                codes.size != 1 || codes.single().second.isBlank() || codes.single().second.length > 2048)
                Result.Invalid
            else Result.Code(codes.single().second)
        }
    } catch (_: Exception) { Result.Invalid }

    fun matchesPendingAccount(pendingEmail: String?, verifiedEmail: String?): Boolean =
        !pendingEmail.isNullOrBlank() && !verifiedEmail.isNullOrBlank() &&
            pendingEmail.trim().equals(verifiedEmail.trim(), ignoreCase = true)

    /** No session is adopted until the server-verified identity matches the signup. */
    suspend fun <S> complete(
        code: String,
        pendingEmail: String,
        exchange: suspend (String) -> S,
        verify: suspend (S) -> Pair<S, String?>,
        adopt: suspend (S) -> Unit,
    ) {
        require(pendingEmail.isNotBlank())
        val (verifiedSession, verifiedEmail) = verify(exchange(code))
        require(matchesPendingAccount(pendingEmail, verifiedEmail))
        adopt(verifiedSession)
    }
}
