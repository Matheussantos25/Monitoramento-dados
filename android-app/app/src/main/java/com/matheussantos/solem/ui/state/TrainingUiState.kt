package com.matheussantos.solem.ui.state

import com.matheussantos.solem.data.model.TrainingRecord

sealed interface TrainingUiState {
    data object Loading : TrainingUiState
    data class Ready(val records: List<TrainingRecord>) : TrainingUiState
    data class Empty(val message: String = "Nenhum registro encontrado.") : TrainingUiState
    data class Error(val message: String) : TrainingUiState
    data object SetupRequired : TrainingUiState
}
