package com.matheussantos.solem.data

import com.matheussantos.solem.BuildConfig
import io.github.jan.supabase.auth.Auth
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.realtime.Realtime
import io.github.jan.supabase.SupabaseClient

object SupabaseProvider {
    val isConfigured: Boolean
        get() = BuildConfig.SUPABASE_URL.startsWith("https://") && BuildConfig.SUPABASE_PUBLISHABLE_KEY.isNotBlank()

    val client: SupabaseClient by lazy {
        check(isConfigured) { "Supabase não configurado. Preencha android-app/local.properties." }
        createSupabaseClient(BuildConfig.SUPABASE_URL, BuildConfig.SUPABASE_PUBLISHABLE_KEY) {
            install(Auth)
            install(Postgrest)
            install(Realtime)
        }
    }
}
