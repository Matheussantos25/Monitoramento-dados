import java.util.Properties
import java.util.Base64

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

android {
    namespace = "com.matheussantos.solem"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.matheussantos.solem"
        minSdk = 26
        targetSdk = 36
        versionCode = 11
        versionName = "0.9.2"
    }

    val properties = Properties()
    val localPropertiesFile = rootProject.file("local.properties")
    if (localPropertiesFile.exists()) {
        localPropertiesFile.inputStream().use { input -> properties.load(input) }
    }
    val mobileKey = properties.getProperty("SUPABASE_PUBLISHABLE_KEY", "")
    val payload = runCatching { String(Base64.getUrlDecoder().decode(mobileKey.split('.').getOrElse(1) { "" }), Charsets.UTF_8) }.getOrDefault("")
    require(!mobileKey.startsWith("sb_secret_") && !payload.contains("service_role")) {
        "Use somente a chave publicável/anon do Supabase. Chaves administrativas não podem entrar no APK."
    }
    fun localValue(name: String) = properties.getProperty(name, "").replace("\\", "\\\\").replace("\"", "\\\"")
    val signingProperties = Properties()
    val signingPropertiesFile = rootProject.file("keystore.properties")
    if (signingPropertiesFile.exists()) {
        signingPropertiesFile.inputStream().use { input -> signingProperties.load(input) }
    }

    buildFeatures { compose = true; buildConfig = true }
    signingConfigs {
        create("release") {
            val storePath = signingProperties.getProperty("storeFile")
            if (!storePath.isNullOrBlank()) {
                storeFile = rootProject.file(storePath)
                storePassword = signingProperties.getProperty("storePassword")
                keyAlias = signingProperties.getProperty("keyAlias")
                keyPassword = signingProperties.getProperty("keyPassword")
            }
        }
    }
    buildTypes {
        debug { buildConfigField("String", "SUPABASE_URL", "\"${localValue("SUPABASE_URL")}\""); buildConfigField("String", "SUPABASE_PUBLISHABLE_KEY", "\"${localValue("SUPABASE_PUBLISHABLE_KEY")}\"") }
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            buildConfigField("String", "SUPABASE_URL", "\"${localValue("SUPABASE_URL")}\"")
            buildConfigField("String", "SUPABASE_PUBLISHABLE_KEY", "\"${localValue("SUPABASE_PUBLISHABLE_KEY")}\"")
            if (signingProperties.getProperty("storeFile") != null) signingConfig = signingConfigs.getByName("release")
        }
    }
}

dependencies {
    implementation("io.noties.markwon:core:4.6.2")
    implementation(platform("androidx.compose:compose-bom:2026.06.00"))
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.runtime:runtime-saveable")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.navigation:navigation-compose:2.8.9")
    implementation("androidx.compose.material:material-icons-extended")

    implementation(platform("io.github.jan-tennert.supabase:bom:3.5.0"))
    implementation("io.github.jan-tennert.supabase:postgrest-kt")
    implementation("io.github.jan-tennert.supabase:realtime-kt")
    implementation("io.github.jan-tennert.supabase:auth-kt")
    implementation("io.github.jan-tennert.supabase:storage-kt")
    implementation("io.ktor:ktor-client-okhttp:3.0.3")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
    debugImplementation("androidx.compose.ui:ui-tooling")
    testImplementation("junit:junit:4.13.2")
}
