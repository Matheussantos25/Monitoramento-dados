package com.matheussantos.solem.ui

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ExpandMore
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.RadioButtonUnchecked
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import java.text.Normalizer
import androidx.compose.ui.Alignment
import androidx.compose.ui.text.style.TextOverflow

@Composable fun Page(title: String, content: @Composable ColumnScope.() -> Unit) {
    Box(Modifier.fillMaxSize(),contentAlignment=Alignment.TopCenter) {
    Column(Modifier.widthIn(max=720.dp).fillMaxWidth().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text(title, style = MaterialTheme.typography.headlineMedium)
        content()
        Spacer(Modifier.height(24.dp))
    }
    }
}
@Composable fun Panel(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(Modifier.fillMaxWidth(), shape=MaterialTheme.shapes.large,
        colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.surfaceContainer)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            content()
        }
    }
}
@Composable fun Field(label: String, value: String, number: Boolean = false, onChange: (String) -> Unit) {
    OutlinedTextField(value, onChange, Modifier.fillMaxWidth(), shape=MaterialTheme.shapes.small, label = { Text(label) }, singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = if (number) KeyboardType.Decimal else KeyboardType.Text))
}
@Composable fun Choice(label: String, selected: String, options: List<String>, onChange: (String) -> Unit) {
    var show by remember { mutableStateOf(false) }
    SelectionField(label,selected.ifBlank {"Selecionar"}) {show=true}
    if(show) SelectionSheet(label,options.distinct(),setOf(selected),false,{show=false}) {onChange(it);show=false}
}
@Composable fun MultiChoice(label: String, selected: List<String>, options: List<String>, onChange: (List<String>) -> Unit) {
    var show by remember { mutableStateOf(false) }
    SelectionField(label,if(selected.isEmpty()) "Selecionar" else selected.joinToString(", ")) {show=true}
    if(show) SelectionSheet(label,(options+selected).distinct(),selected.toSet(),true,{show=false}) {item ->
        onChange(if(item in selected) selected-item else selected+item)
    }
}

@Composable private fun SelectionField(label:String,value:String,onClick:()->Unit) {
    Surface(onClick=onClick,modifier=Modifier.fillMaxWidth(),shape=MaterialTheme.shapes.small,
        color=MaterialTheme.colorScheme.surfaceContainer,border=BorderStroke(1.dp,MaterialTheme.colorScheme.outline)) {
        Row(Modifier.padding(horizontal=16.dp,vertical=12.dp),verticalAlignment=Alignment.CenterVertically) {
            Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(5.dp)) {
                Text(label,style=MaterialTheme.typography.labelMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
                Text(value,style=MaterialTheme.typography.bodyLarge,maxLines=2,overflow=TextOverflow.Ellipsis)
            }
            Icon(Icons.Outlined.ExpandMore,"Selecionar $label",Modifier.padding(start=8.dp))
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun SelectionSheet(title:String,options:List<String>,selected:Set<String>,multiple:Boolean,
    dismiss:()->Unit,select:(String)->Unit) {
    var query by remember { mutableStateOf("") }
    ModalBottomSheet(onDismissRequest=dismiss,sheetState=rememberModalBottomSheetState(skipPartiallyExpanded=true)) {
        Column(Modifier.fillMaxWidth().padding(horizontal=20.dp).imePadding(),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Text(title,style=MaterialTheme.typography.titleLarge)
            if(options.size>8) OutlinedTextField(query,{query=it},modifier=Modifier.fillMaxWidth(),
                label={Text("Buscar $title")},leadingIcon={Icon(Icons.Outlined.Search,null)},singleLine=true,
                shape=MaterialTheme.shapes.small)
            fun normalized(value:String)=Normalizer.normalize(value,Normalizer.Form.NFD).replace(Regex("\\p{M}+"),"").lowercase(java.util.Locale.ROOT)
            val filtered=options.filter {normalized(it).contains(normalized(query.trim()))}
            Text("${filtered.size} opções · ${if(multiple) "selecione uma ou mais" else "toque para escolher"}",
                style=MaterialTheme.typography.labelMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
            if(filtered.isEmpty()) Text("Nenhuma opção encontrada.",color=MaterialTheme.colorScheme.onSurfaceVariant)
            LazyColumn(Modifier.fillMaxWidth().heightIn(max=360.dp)) {
                items(filtered,key={it}) {item ->
                    val chosen=item in selected
                    ListItem(headlineContent={Text(item)},modifier=Modifier
                        .semantics {this.selected=chosen}.clickable(role=if(multiple) Role.Checkbox else Role.RadioButton) {select(item)},
                        colors=ListItemDefaults.colors(containerColor=if(chosen) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceContainerLow),
                        trailingContent={if(multiple) Checkbox(chosen,null) else Icon(if(chosen) Icons.Outlined.Check else Icons.Outlined.RadioButtonUnchecked,
                            if(chosen) "Selecionado" else null,tint=if(chosen) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline)})
                }
            }
            TextButton(dismiss,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)) {Text(if(multiple) "Concluir seleção" else "Fechar")}
            Spacer(Modifier.height(16.dp))
        }
    }
}
@Composable fun Goal(label: String, value: Double, target: Int, unit: String = "", decimals: Int = 0) {
    val amount = if (decimals > 0) "%1$.${decimals}f".format(value) else "%.0f".format(value)
    Text("$label: $amount / $target${if (unit.isBlank()) "" else " $unit"}")
    LinearProgressIndicator(progress = { (value / target).toFloat().coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth())
}
