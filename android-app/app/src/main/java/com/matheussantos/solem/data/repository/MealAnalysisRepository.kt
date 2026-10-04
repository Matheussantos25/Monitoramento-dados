package com.matheussantos.solem.data.repository

import android.util.Base64
import com.matheussantos.solem.BuildConfig
import com.matheussantos.solem.domain.*
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.auth
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.*
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.MediaType.Companion.toMediaType
import java.util.concurrent.TimeUnit

class MealAnalysisRepository(private val client: SupabaseClient, private val catalog: List<MealReference>) {
    private val http=OkHttpClient.Builder().callTimeout(65,TimeUnit.SECONDS).retryOnConnectionFailure(false).build()
    suspend fun recognize(raw: ByteArray): MealEstimate = withContext(Dispatchers.IO) {
        val session=client.auth.currentSessionOrNull() ?: throw IllegalArgumentException("Sua sessão expirou. Entre novamente.")
        val jpeg=PhotoRepository(client).normalize(raw)
        val payload=buildJsonObject {
            put("action","recognize"); put("mime_type","image/jpeg")
            put("image",Base64.encodeToString(jpeg,Base64.NO_WRAP)); put("consent_version",MEAL_CONSENT); put("adult",true)
        }
        val request=Request.Builder().url(BuildConfig.SUPABASE_URL.trimEnd('/')+"/functions/v1/meal-analysis")
            .header("apikey",BuildConfig.SUPABASE_PUBLISHABLE_KEY).header("Authorization","Bearer ${session.accessToken}")
            .post(payload.toString().toRequestBody("application/json".toMediaType())).build()
        http.newCall(request).execute().use { response ->
            val result=runCatching { mealJson.parseToJsonElement(response.body?.string().orEmpty()).jsonObject }.getOrNull()
            if(!response.isSuccessful) {
                val code=result?.get("code")?.jsonPrimitive?.content.orEmpty()
                val message=when {
                    response.code==401 -> "Sua sessão expirou. Entre novamente."
                    response.code==404 || code=="not_configured" -> "O reconhecimento ainda precisa da chave gratuita configurada no backend."
                    response.code==429 -> "Limite gratuito ou intervalo entre análises atingido. Aguarde; o registro manual continua disponível."
                    code=="not_food" -> "Não foi possível identificar uma refeição. Use uma foto nítida do prato."
                    code=="personal_content" -> "Use somente o prato, sem rostos, documentos ou identificação pessoal."
                    code=="invalid_image" -> "Escolha uma imagem válida de até 8 MB e 20 megapixels."
                    else -> "Análise indisponível. Tente depois ou registre manualmente."
                }
                throw IllegalArgumentException(message)
            }
            require(result!=null) { "A análise não foi concluída. Tente outra foto." }
            val items=mealJson.decodeFromJsonElement<List<MealFood>>(result.getValue("items"))
            calculateMeal(items,catalog) // Never trust AI totals or unknown catalog identifiers.
        }
    }
}
