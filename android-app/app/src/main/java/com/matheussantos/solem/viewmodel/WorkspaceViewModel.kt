package com.matheussantos.solem.viewmodel

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.matheussantos.solem.data.SupabaseProvider
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.data.model.ProgressPhoto
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.data.repository.PhotoRepository
import com.matheussantos.solem.data.repository.HealthRepository
import com.matheussantos.solem.data.repository.WorkspaceRepository
import com.matheussantos.solem.domain.MAX_PDF_BYTES
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.auth.providers.builtin.Email
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.io.ByteArrayOutputStream
import kotlinx.serialization.json.JsonObject

data class WorkspaceState(val initialized: Boolean = false, val signedIn: Boolean = false, val busy: Boolean = false,
    val items: List<PersonalItem> = emptyList(), val photos: List<ProgressPhoto> = emptyList(),
    val healthEntries: List<HealthEntry> = emptyList(),
    val photoData: Map<String, ByteArray> = emptyMap(), val message: String? = null, val failed: Boolean = false)
class WorkspaceViewModel(application: Application): AndroidViewModel(application) {
    private var repository: WorkspaceRepository? = null
    private val repo get() = repository ?: WorkspaceRepository().also { repository=it }
    private val photoRepo get() = PhotoRepository(repo.client)
    private val healthRepo get() = HealthRepository(repo.client)
    private val mutableState = MutableStateFlow(WorkspaceState())
    val state = mutableState.asStateFlow()
    init {
        if (!SupabaseProvider.isConfigured) {
            mutableState.value = WorkspaceState(initialized=true,message="Configure a URL e a chave pública do Supabase.",failed=true)
        } else viewModelScope.launch {
            try {
                repo.client.auth.awaitInitialization()
                val logged = repo.client.auth.currentSessionOrNull() != null
                mutableState.update { it.copy(initialized=true,signedIn=logged) }
                if (logged) load()
            } catch (e: CancellationException) { throw e }
            catch (_: Exception) {
                mutableState.value = WorkspaceState(initialized=true,message="Não foi possível restaurar sua sessão. Entre novamente.",failed=true)
            }
        }
    }
    private fun action(block: suspend () -> Unit) {
        if (state.value.busy) return
        if (!SupabaseProvider.isConfigured) { mutableState.update { it.copy(initialized=true,message="Configure a URL e a chave pública do Supabase.",failed=true) }; return }
        viewModelScope.launch {
            mutableState.update { it.copy(busy=true,message=null,failed=false) }
            try { block() }
            catch (e: CancellationException) { throw e }
            catch (e: Exception) {
                val logged = repo.client.auth.currentSessionOrNull() != null
                mutableState.update { it.copy(initialized=true,signedIn=logged, items=if(logged) it.items else emptyList(), failed=true,
                    message=if(e is IllegalArgumentException) e.message else "Não foi possível concluir. Confira sua conexão e sessão. Se enviou PDF, tente baixá-lo antes de reenviar.") }
            } finally { mutableState.update { it.copy(busy=false) } }
        }
    }
    fun login(email: String, password: String, signup: Boolean) = action {
        if (signup) repo.client.auth.signUpWith(Email) { this.email=email.trim(); this.password=password }
        else repo.client.auth.signInWith(Email) { this.email=email.trim(); this.password=password }
        val logged = repo.client.auth.currentUserOrNull() != null
        mutableState.update { it.copy(initialized=true,signedIn=logged,items=emptyList(),message=if(!logged) "Confira seu e-mail para confirmar o cadastro e depois entre." else null) }
        if(logged) load()
    }
    private suspend fun load() { val rows = repo.list(); mutableState.update { it.copy(items=rows) } }
    fun refresh() = action { load() }
    fun logout() = action {
        runCatching { repo.client.auth.signOut() }
        runCatching { repo.client.close() }
        repository=null
        mutableState.value=WorkspaceState(initialized=true,message="Sessão encerrada.")
    }
    fun save(item: PersonalItem, old: PersonalItem?, done: (PersonalItem) -> Unit) = action {
        val saved = repo.save(item,old)
        // Reflect confirmed write even if the subsequent refresh fails.
        mutableState.update { it.copy(items=it.items.filterNot { x -> x.id==saved.id } + saved, message="Salvo no Supabase. Atualize no outro dispositivo.") }
        done(saved)
    }
    fun archive(item: PersonalItem) = action { repo.archive(item,!item.archived); load() }
    fun loadHealth() = action { mutableState.update { it.copy(healthEntries=healthRepo.list()) } }
    fun saveHealth(day: String, time: String, kind: String, details: JsonObject, id: String? = null) = action {
        healthRepo.save(day, time, kind, details, id)
        mutableState.update { it.copy(healthEntries=healthRepo.list(), message="Diário privado atualizado.") }
    }
    fun deleteHealth(id: String) = action {
        healthRepo.delete(id)
        mutableState.update { it.copy(healthEntries=healthRepo.list(), message="Registro removido do diário privado.") }
    }
    fun loadPhotos() = action { mutableState.update { it.copy(photos=photoRepo.list()) } }
    fun loadPhotoBytes(selected: List<ProgressPhoto>) = action {
        val pending = selected.distinctBy { it.id }.filterNot { it.id in state.value.photoData }
        pending.forEach { photo ->
            val bytes = photoRepo.download(photo)
            mutableState.update { current -> current.copy(photoData=(current.photoData + (photo.id to bytes)).entries.toList()
                .takeLast(4).associate { it.key to it.value }) }
        }
    }
    fun uploadPhoto(day: String, kind: String, uri: Uri) = action {
        require(state.value.photos.none { it.day == day && it.kind == kind }) { "Já há uma foto deste tipo neste dia. Remova-a antes de trocar." }
        val bytes = withContext(Dispatchers.IO) {
            getApplication<Application>().contentResolver.openInputStream(uri)?.use { input ->
                val output = ByteArrayOutputStream()
                val buffer = ByteArray(8192)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    require(output.size() + count <= 8 * 1024 * 1024) { "Selecione uma imagem de até 8 MB." }
                    output.write(buffer, 0, count)
                }
                output.toByteArray()
            } ?: throw IllegalArgumentException("Não foi possível abrir a imagem selecionada.")
        }
        photoRepo.upload(day, kind, bytes)
        mutableState.update { it.copy(photos=photoRepo.list(), message="Foto salva em armazenamento privado.") }
    }
    fun deletePhoto(photo: ProgressPhoto) = action {
        photoRepo.delete(photo)
        mutableState.update { it.copy(photos=photoRepo.list(), photoData=it.photoData - photo.id,
            message="Foto removida permanentemente.") }
    }
    fun upload(item: PersonalItem, uri: Uri) = action {
        val bytes = withContext(Dispatchers.IO) {
            getApplication<Application>().contentResolver.openInputStream(uri)?.use { input ->
                val output = ByteArrayOutputStream()
                val buffer = ByteArray(8192)
                while(true) {
                    val n=input.read(buffer)
                    if(n<0) break
                    require(output.size()+n<=MAX_PDF_BYTES) { "O PDF deve ter até 10 MB." }
                    output.write(buffer,0,n)
                }
                output.toByteArray()
            } ?: throw IllegalArgumentException("Não foi possível abrir o arquivo selecionado.")
        }
        repo.upload(item,bytes)
        mutableState.update { it.copy(message="PDF enviado para armazenamento privado.") }
    }
    fun export(item: PersonalItem, uri: Uri) = action {
        val bytes = repo.download(item)
        withContext(Dispatchers.IO) {
            getApplication<Application>().contentResolver.openOutputStream(uri)?.use { it.write(bytes) }
                ?: throw IllegalArgumentException("Não foi possível gravar no destino selecionado.")
        }
        mutableState.update { it.copy(message="PDF exportado. A cópia no destino escolhido não é protegida pelo login do Solem.") }
    }
}
