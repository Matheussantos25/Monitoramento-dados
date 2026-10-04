package com.matheussantos.solem.viewmodel

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.matheussantos.solem.data.repository.MealAnalysisRepository
import com.matheussantos.solem.domain.*
import io.github.jan.supabase.SupabaseClient
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.io.ByteArrayOutputStream

data class MealPhotoState(val source: Uri? = null, val busy: Boolean = false,
    val draft: MealEstimate? = null, val revision: Int = 0, val message: String? = null)
class MealAnalysisViewModel(application: Application, client: SupabaseClient): AndroidViewModel(application) {
    val catalog: List<MealReference> = mealJson.decodeFromString(application.assets.open("nutrition_catalog.json")
        .bufferedReader().use { it.readText() })
    private val repo=MealAnalysisRepository(client,catalog)
    private var job: Job?=null
    private val mutable=MutableStateFlow(MealPhotoState())
    val state=mutable.asStateFlow()
    fun select(uri: Uri?) { clear(); mutable.update { it.copy(source=uri) } }
    fun clear() { job?.cancel(); mutable.value=MealPhotoState(revision=mutable.value.revision+1) }
    fun analyze(consent: Boolean, adult: Boolean) {
        val uri=state.value.source ?: return
        if(state.value.busy || !consent || !adult) return
        job=viewModelScope.launch {
            mutable.update { it.copy(busy=true,message=null) }
            try {
                val raw=withContext(Dispatchers.IO) {
                    getApplication<Application>().contentResolver.openInputStream(uri)?.use { input ->
                        val output=ByteArrayOutputStream(); val buffer=ByteArray(8192)
                        while(true) {
                            val read=input.read(buffer); if(read<0) break
                            require(output.size()+read<=8*1024*1024) { "Escolha uma foto de até 8 MB." }
                            output.write(buffer,0,read)
                        }
                        output.toByteArray()
                    } ?: throw IllegalArgumentException("Não foi possível abrir esta foto. Escolha-a novamente.")
                }
                val estimate=repo.recognize(raw)
                mutable.update { it.copy(busy=false,draft=estimate,revision=it.revision+1) }
            } catch(e: CancellationException) { throw e }
            catch(e: Exception) {
                mutable.update { it.copy(busy=false,message=if(e is IllegalArgumentException) e.message
                    else "Não foi possível analisar. Confira a conexão; o registro manual continua disponível.") }
            }
        }
    }
}
