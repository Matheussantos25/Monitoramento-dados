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
import io.github.jan.supabase.auth.providers.builtin.OTP
import io.github.jan.supabase.auth.OtpType
import io.github.jan.supabase.auth.status.SessionStatus
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.io.ByteArrayOutputStream
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.*
import com.matheussantos.solem.domain.genericAccount
import com.matheussantos.solem.domain.EmailConfirmation
import com.matheussantos.solem.domain.EmailAccess
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

data class WorkspaceState(val initialized: Boolean = false, val signedIn: Boolean = false, val busy: Boolean = false,
    val accountId: String = "", val generic: Boolean = true,
    val sessionGeneration: Int = 0,
    val emailChallenge: String = "", val resendAvailableAt: Long = 0L, val emailSending: Boolean = false,
    val items: List<PersonalItem> = emptyList(), val photos: List<ProgressPhoto> = emptyList(),
    val healthEntries: List<HealthEntry> = emptyList(),
    val healthLoaded: Boolean = false, val healthFailed: Boolean = false,
    val photoData: Map<String, ByteArray> = emptyMap(), val message: String? = null, val failed: Boolean = false)
class WorkspaceViewModel(application: Application): AndroidViewModel(application) {
    private fun accountState(): Pair<String, Boolean> {
        val user = repo.client.auth.currentUserOrNull()
        val defaults = Json.parseToJsonElement(getApplication<Application>().assets.open("account_defaults.json").bufferedReader().use { it.readText() }).jsonObject
        return user?.id.orEmpty() to genericAccount(user?.email, user?.createdAt?.toString(),
            defaults.getValue("preserved_email").jsonPrimitive.content, defaults.getValue("new_accounts_since").jsonPrimitive.content)
    }
    private var repository: WorkspaceRepository? = null
    private val repo get() = repository ?: WorkspaceRepository().also { repository=it }
    val trainingClient get() = repo.client
    val trainingTable get(): String {
        val defaults = Json.parseToJsonElement(getApplication<Application>().assets.open("account_defaults.json").bufferedReader().use { it.readText() }).jsonObject
        return com.matheussantos.solem.domain.activityTable(repo.client.auth.currentUserOrNull()?.email,
            defaults.getValue("preserved_email").jsonPrimitive.content)
    }
    private val photoRepo get() = PhotoRepository(repo.client)
    private val healthRepo get() = HealthRepository(repo.client)
    private val mutableState = MutableStateFlow(WorkspaceState())
    val state = mutableState.asStateFlow()
    private val authMutex = Mutex()
    private var restoreJob: Job? = null
    private var confirmationJob: Job? = null
    private val pendingSignup = application.getSharedPreferences("solem_pending_signup", android.content.Context.MODE_PRIVATE)
    private var authWatcher: Job? = null
    private fun watchSession() {
        authWatcher?.cancel()
        val sessionClient = repo.client
        authWatcher = viewModelScope.launch {
            sessionClient.auth.sessionStatus.collect { status ->
                mutableState.update { it.afterAuthStatus(status) }
            }
        }
    }
    init {
        if (!SupabaseProvider.isConfigured) {
            mutableState.value = WorkspaceState(initialized=true,message="Configure a URL e a chave pública do Supabase.",failed=true)
        } else restoreJob = viewModelScope.launch {
            try {
                repo.client.auth.awaitInitialization()
                // The SDK restores/persists and refreshes credentials. A temporary
                // network failure is not a reason to discard that login. Wait for
                // a definitive result if a cold-start refresh is still retrying.
                repo.client.auth.sessionStatus.onEach { status ->
                    if (status is SessionStatus.RefreshFailure) mutableState.update {
                        it.copy(message="Aguardando conexão para recuperar seu acesso…")
                    }
                }.first {
                    it is SessionStatus.Authenticated || it is SessionStatus.NotAuthenticated
                }
                val (id, generic) = accountState()
                val logged = repo.client.auth.currentSessionOrNull() != null && id.isNotBlank()
                val pendingEmail = if (!logged && pendingSignup.getString("mode", null) == "otp") pendingSignup.getString("email", "").orEmpty() else ""
                mutableState.update { it.copy(initialized=true,signedIn=logged,accountId=id,generic=generic,message=null,
                    emailChallenge=pendingEmail,resendAvailableAt=pendingSignup.getLong("resend_at", 0L)) }
                watchSession()
            } catch (e: CancellationException) { throw e }
            catch (_: Exception) {
                mutableState.value = WorkspaceState(initialized=true,message="Não foi possível restaurar sua sessão. Entre novamente.",failed=true)
            }
            // Loading app data must never turn a restored session into a logout.
            if (state.value.signedIn) {
                try { load() }
                catch (e: CancellationException) { throw e }
                catch (_: Exception) {
                    mutableState.update { it.copy(failed=true,message="Você continua conectado. Não foi possível carregar os dados; tente atualizar quando a conexão voltar.") }
                }
            }
        }
    }
    private fun action(errorMessage: String? = null, block: suspend () -> Unit) {
        if (state.value.busy) return
        if (!SupabaseProvider.isConfigured) { mutableState.update { it.copy(initialized=true,message="Configure a URL e a chave pública do Supabase.",failed=true) }; return }
        viewModelScope.launch {
            authMutex.withLock {
            mutableState.update { it.copy(busy=true,message=null,failed=false) }
            try { block() }
            catch (e: CancellationException) { throw e }
            catch (e: Exception) {
                mutableState.update { it.afterAuthStatus(repo.client.auth.sessionStatus.value).copy(initialized=true, failed=true,
                    message=errorMessage ?: if(e is IllegalArgumentException) e.message else "Não foi possível concluir. Confira sua conexão e sessão. Se enviou PDF, tente baixá-lo antes de reenviar.") }
            } finally { mutableState.update { it.copy(busy=false,emailSending=false) } }
            }
        }
    }
    fun login(email: String, password: String, signup: Boolean) = action("Não foi possível entrar. Confira e-mail, senha e conexão. Você também pode entrar com um código por e-mail.") {
        // A failed sign-in or pending confirmation must never revive a previous account.
        val generation = state.value.sessionGeneration + 1
        mutableState.value = WorkspaceState(initialized=true, busy=true, sessionGeneration=generation)
        if (repo.client.auth.currentSessionOrNull() != null) {
            try { repo.client.auth.signOut() }
            finally { withContext(NonCancellable) { repo.client.auth.clearSession() } }
        }
        if (signup) {
            // Persist only the expected email, never the password or callback code.
            pendingSignup.edit().putString("email", email.trim()).apply()
            repo.client.auth.signUpWith(Email, redirectUrl=EmailConfirmation.REDIRECT_URL) {
                this.email=email.trim(); this.password=password
            }
        }
        else repo.client.auth.signInWith(Email) { this.email=email.trim(); this.password=password }
        val logged = repo.client.auth.currentSessionOrNull() != null &&
            repo.client.auth.currentUserOrNull()?.email?.equals(email.trim(), ignoreCase=true) == true
        val (id, generic) = accountState()
        mutableState.update { it.copy(initialized=true,signedIn=logged,accountId=id,generic=generic,items=emptyList(),photos=emptyList(),photoData=emptyMap(),healthEntries=emptyList(),healthLoaded=false,healthFailed=false,
            message=if(!logged) "Abra o e-mail neste celular e toque em confirmar. O link retornará ao Solem. Se o navegador perguntar, escolha abrir no aplicativo." else null) }
        if(logged) { pendingSignup.edit().clear().apply(); watchSession(); load() }
    }
    fun requestEmailAccess(rawEmail: String) = action("Não foi possível enviar o código agora. Confira a conexão ou aguarde alguns minutos e tente novamente.") {
        if (state.value.signedIn) return@action
        val email = EmailAccess.normalizeEmail(rawEmail)
        require(EmailAccess.validEmail(email))
        if (EmailAccess.resendSeconds(state.value.resendAvailableAt, System.currentTimeMillis()) > 0) {
            mutableState.update { it.copy(message="Aguarde um minuto entre os envios.") }
            return@action
        }
        // The same request signs in an existing user OR creates an unconfirmed account.
        // Never probe for account existence or initialize/overwrite personal records here.
        val resendAt = System.currentTimeMillis() + EmailAccess.RESEND_DELAY_MS
        mutableState.value = WorkspaceState(initialized=true,busy=true,emailSending=true,
            emailChallenge=state.value.emailChallenge.takeIf { it == email }.orEmpty(),
            sessionGeneration=state.value.sessionGeneration+1,resendAvailableAt=resendAt)
        if (repo.client.auth.currentSessionOrNull() != null) {
            try { repo.client.auth.signOut() }
            finally { withContext(NonCancellable) { repo.client.auth.clearSession() } }
        }
        pendingSignup.edit().putString("email",email).putString("mode","sending").putLong("resend_at",resendAt).apply()
        repo.client.auth.signInWith(OTP, redirectUrl=EmailConfirmation.REDIRECT_URL) {
            this.email=email
            createUser=true
        }
        pendingSignup.edit().putString("mode","otp").apply()
        mutableState.update { it.copy(emailChallenge=email,message=null) }
    }
    fun verifyEmailAccess(rawCode: String) = action("Não foi possível confirmar. Confira o código mais recente e a conexão. Se ele expirou, solicite outro.") {
        if (state.value.signedIn) return@action
        val email = state.value.emailChallenge
        require(EmailAccess.validCode(rawCode))
        require(EmailConfirmation.matchesPendingAccount(pendingSignup.getString("email",null),email))
        try {
            repo.client.auth.verifyEmailOtp(type=OtpType.Email.EMAIL,email=email,token=rawCode.trim())
            val user = repo.client.auth.retrieveUserForCurrentSession(updateSession=true)
            require(EmailConfirmation.matchesPendingAccount(email,user.email))
        } catch (e: Exception) {
            // The SDK imports successful verification automatically; don't expose it in
            // the UI until its identity has been checked against the requested email.
            withContext(NonCancellable) {
                if (repo.client.auth.currentSessionOrNull()!=null) repo.client.auth.clearSession()
            }
            throw e
        }
        val (id, generic) = accountState()
        pendingSignup.edit().clear().apply()
        mutableState.value = WorkspaceState(initialized=true,signedIn=true,busy=true,accountId=id,generic=generic,
            sessionGeneration=state.value.sessionGeneration+1)
        watchSession()
        try { load() }
        catch (e: CancellationException) { throw e }
        catch (_: Exception) { mutableState.update { it.copy(failed=true,message="Você entrou. Não foi possível carregar os dados; tente atualizar.") } }
    }
    fun changeAccessEmail() {
        if (state.value.busy || state.value.signedIn) return
        pendingSignup.edit().remove("email").remove("mode").apply()
        mutableState.update { it.copy(emailChallenge="",message=null,failed=false) }
    }
    fun confirmEmail(url: String) {
        val callback = EmailConfirmation.parse(url)
        if (callback == EmailConfirmation.Result.Ignore || confirmationJob?.isActive == true) return
        confirmationJob = viewModelScope.launch {
            restoreJob?.join() // Cold start: never race persisted-session initialization.
            authMutex.withLock {
                if (!SupabaseProvider.isConfigured || state.value.signedIn) return@withLock
                val pendingEmail = pendingSignup.getString("email", null)
                if (callback !is EmailConfirmation.Result.Code || pendingEmail.isNullOrBlank()) {
                    mutableState.update { it.copy(initialized=true,failed=true,
                        message="Não foi possível concluir pelo link. Informe seu e-mail para receber um novo código, ou entre com sua senha existente. Abra o link no celular onde solicitou o acesso.") }
                    return@withLock
                }
                mutableState.value = WorkspaceState(initialized=true,busy=true,
                    sessionGeneration=state.value.sessionGeneration+1,message="Confirmando seu acesso…")
                try {
                    // PKCE binds the code to this installation. Validate with Auth before
                    // importing the session so a different account can never be adopted.
                    EmailConfirmation.complete(callback.value, pendingEmail,
                        exchange={ repo.client.auth.exchangeCodeForSession(it, saveSession=false) },
                        verify={ session ->
                            val user = repo.client.auth.retrieveUser(session.accessToken)
                            session.copy(user=user) to user.email
                        },
                        adopt={ repo.client.auth.importSession(it) })
                    val (id, generic) = accountState()
                    mutableState.update { it.copy(signedIn=true,accountId=id,generic=generic,emailChallenge="",resendAvailableAt=0L,message="E-mail confirmado. Bem-vindo ao Solem.") }
                    pendingSignup.edit().clear().apply()
                    watchSession()
                    try { load() }
                    catch (e: CancellationException) { throw e }
                    catch (_: Exception) { mutableState.update { it.copy(failed=true,message="Acesso confirmado. Não foi possível carregar os dados; tente atualizar.") } }
                } catch (e: CancellationException) { throw e }
                catch (_: Exception) {
                    mutableState.update { it.copy(emailChallenge=pendingEmail,failed=true,message="Não foi possível concluir pelo link. Ele pode ter expirado, já ter sido usado ou a conexão falhou. Tente o código do e-mail ou solicite outro.") }
                } finally { mutableState.update { it.copy(busy=false) } }
            }
        }
    }
    private suspend fun load() {
        val account = state.value.accountId
        val generation = state.value.sessionGeneration
        val rows = repo.list()
        mutableState.update {
            if(it.signedIn && it.accountId == account && it.sessionGeneration == generation) it.copy(items=rows) else it
        }
    }
    fun refresh() = action { load() }
    fun logout() = action {
        val generation = state.value.sessionGeneration + 1
        mutableState.value=WorkspaceState(initialized=true,busy=true,sessionGeneration=generation)
        authWatcher?.cancel()
        pendingSignup.edit().clear().apply()
        runCatching { repo.client.auth.signOut() }
        repo.client.auth.clearSession() // Also clear persisted credentials if revocation failed offline.
        runCatching { repo.client.close() }
        repository=null
        mutableState.value=WorkspaceState(initialized=true,sessionGeneration=generation,message="Sessão encerrada.")
    }
    fun save(item: PersonalItem, old: PersonalItem?, done: (PersonalItem) -> Unit) = action {
        val saved = repo.save(item,old)
        // Reflect confirmed write even if the subsequent refresh fails.
        mutableState.update { it.copy(items=it.items.filterNot { x -> x.id==saved.id } + saved, message="Salvo no Supabase. Atualize no outro dispositivo.") }
        done(saved)
    }
    fun archive(item: PersonalItem) = action { repo.archive(item,!item.archived); load() }
    fun loadHealth() = action {
        try { val rows=healthRepo.list();mutableState.update { it.copy(healthEntries=rows,healthLoaded=true,healthFailed=false) } }
        catch(e:CancellationException) {throw e}
        catch(e:Exception) {mutableState.update { it.copy(healthLoaded=true,healthFailed=true) };throw e}
    }
    fun saveHealth(day: String, time: String, kind: String, details: JsonObject, id: String? = null, onSaved: () -> Unit = {}) = action {
        healthRepo.save(day, time, kind, details, id)
        onSaved() // Clear a photo draft only after the write succeeds, before refresh.
        val rows=healthRepo.list()
        mutableState.update { it.copy(healthEntries=rows,healthLoaded=true,healthFailed=false,message="Diário privado atualizado.") }
    }
    fun deleteHealth(id: String) = action {
        healthRepo.delete(id)
        val rows=healthRepo.list()
        mutableState.update { it.copy(healthEntries=rows,healthLoaded=true,healthFailed=false,message="Registro removido do diário privado.") }
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
