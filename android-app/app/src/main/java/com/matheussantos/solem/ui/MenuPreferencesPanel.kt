package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.selection.toggleable
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.MenuViewModel

@Composable fun MenuPreferencesPanel(vm:MenuViewModel,onboarding:Boolean=false,done:()->Unit={}) {
    val state by vm.state.collectAsState()
    var selection by remember(state.tabs) {mutableStateOf(state.tabs)}
    Panel(if(onboarding) "O que você quer acompanhar?" else "Minhas abas") {
        Text("Escolha as áreas do seu menu. Ocultar uma aba mantém todos os registros. A seleção fica na sua conta e vale também para o site.")
        Text("Visão geral e Personalizar ficam sempre acessíveis. Você pode mudar suas escolhas quando quiser.",style=MaterialTheme.typography.bodySmall)
        if(state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        androidTabIds.forEachIndexed {index,id -> if(id !in pinnedTabs) {
            Row(Modifier.fillMaxWidth().toggleable(value=id in selection,enabled=state.loaded && !state.busy,role=Role.Checkbox,
                onValueChange={selection=if(it)selection+id else selection-id}).padding(vertical=4.dp),verticalAlignment=Alignment.CenterVertically) {
                Checkbox(id in selection,null,enabled=state.loaded && !state.busy)
                Text(pages[index],Modifier.padding(start=12.dp))
            }
        } }
        state.error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
        state.message?.let {Text(it,color=MaterialTheme.colorScheme.primary)}
        Button({vm.save(selection,done)},enabled=state.loaded && !state.busy,modifier=Modifier.fillMaxWidth()) {
            Text(if(onboarding) "Começar com estas abas" else "Salvar minhas abas")
        }
        TextButton(vm::reload,enabled=!state.busy) {Text("Atualizar abas da conta")}
    }
}
