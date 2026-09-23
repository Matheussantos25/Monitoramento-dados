package com.matheussantos.solem.viewmodel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.matheussantos.solem.data.SupabaseProvider
import com.matheussantos.solem.data.model.*
import com.matheussantos.solem.data.repository.TrainingRepository
import com.matheussantos.solem.ui.state.TrainingUiState
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*

class TrainingViewModel : ViewModel() {
    private val repo = TrainingRepository()
    private val mutable = MutableStateFlow<TrainingUiState>(TrainingUiState.Loading)
    val state = mutable.asStateFlow()
    private val notice = MutableStateFlow<String?>(null)
    val message = notice.asStateFlow()
    val busy = MutableStateFlow(false)
    private var refreshJob: Job? = null
    private var refreshAgain = false
    init {
        refresh()
        if (SupabaseProvider.isConfigured) viewModelScope.launch {
            try { repo.observeAll().collect { refresh() } }
            catch (e: CancellationException) { throw e }
            catch (_: Exception) { notice.value = "Atualização automática indisponível. Use Atualizar." }
        }
    }
    fun refresh() {
        if (!SupabaseProvider.isConfigured) { mutable.value = TrainingUiState.SetupRequired; return }
        if (refreshJob?.isActive == true) { refreshAgain = true; return }
        refreshJob = viewModelScope.launch {
            try {
                val rows = repo.fetchAll().sortedWith(compareByDescending<TrainingRecord> { it.data }.thenByDescending { it.horario })
                mutable.value = if (rows.isEmpty()) TrainingUiState.Empty() else TrainingUiState.Ready(rows)
            } catch (e: CancellationException) { throw e }
            catch (_: Exception) {
                if (mutable.value is TrainingUiState.Ready) notice.value = "Não foi possível atualizar. O histórico pode estar desatualizado."
                else mutable.value = TrainingUiState.Error("Não foi possível carregar. Verifique a conexão e as permissões.")
            }
            finally {
                refreshJob = null
                if (refreshAgain && isActive) { refreshAgain = false; refresh() }
            }
        }
    }
    fun save(id: Long?, value: TrainingMutation, done: () -> Unit) = mutate(done) {
        if (id == null) repo.insert(value) else repo.update(id, value)
    }
    fun insertBatch(values: List<TrainingMutation>, done: () -> Unit) = mutate(done) { repo.insertBatch(values) }
    fun delete(id: Long) = mutate({}) { repo.delete(id) }
    private fun mutate(done: () -> Unit, block: suspend () -> Unit) {
        if (busy.value) return
        busy.value = true
        viewModelScope.launch {
            try { block(); notice.value = "Alteração salva."; refreshJob?.cancelAndJoin(); refresh(); done() }
            catch (e: CancellationException) { throw e }
            catch (_: Exception) { notice.value = "Não foi possível confirmar a gravação. Atualize o histórico antes de tentar novamente."; refresh() }
            finally { busy.value = false }
        }
    }
    fun consumeMessage() { notice.value = null }
}
