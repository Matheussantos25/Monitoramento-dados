package com.matheussantos.solem.data

import com.matheussantos.solem.BuildConfig

object SupabaseProvider {
    val isConfigured: Boolean
        get() = BuildConfig.SUPABASE_URL.startsWith("https://") && BuildConfig.SUPABASE_PUBLISHABLE_KEY.isNotBlank()

}
