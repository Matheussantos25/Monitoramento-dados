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

@Composable fun Page(title: String, content: @Composable ColumnScope.() -> Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("SISTEMA / JORNADA", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
        Text(title, style = MaterialTheme.typography.headlineMedium)
        content()
        Spacer(Modifier.height(24.dp))
    }
}
@Composable fun Panel(title: String, content: @Composable ColumnScope.() -> Unit) {
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            content()
        }
    }
}
@Composable fun Field(label: String, value: String, number: Boolean = false, onChange: (String) -> Unit) {
    OutlinedTextField(value, onChange, Modifier.fillMaxWidth(), label = { Text(label) }, singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = if (number) KeyboardType.Decimal else KeyboardType.Text))
}
@Composable fun Choice(label: String, selected: String, options: List<String>, onChange: (String) -> Unit) {
    var show by remember { mutableStateOf(false) }
    OutlinedButton(onClick = { show = true }, modifier = Modifier.fillMaxWidth()) { Text("$label: $selected") }
    if (show) AlertDialog(onDismissRequest = { show = false }, title = { Text(label) }, text = {
        Column(Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState())) {
            options.distinct().forEach { item ->
                TextButton(onClick = { onChange(item); show = false }, modifier = Modifier.fillMaxWidth()) { Text(item) }
            }
        }
    }, confirmButton = { TextButton(onClick = { show = false }) { Text("Fechar") } })
}
@Composable fun MultiChoice(label: String, selected: List<String>, options: List<String>, onChange: (List<String>) -> Unit) {
    var show by remember { mutableStateOf(false) }
    OutlinedButton(onClick = { show = true }, modifier = Modifier.fillMaxWidth()) {
        Text("$label: " + if (selected.isEmpty()) "Selecionar" else selected.joinToString(", "))
    }
    if (show) AlertDialog(onDismissRequest = { show = false }, title = { Text(label) }, text = {
        Column(Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState())) {
            (options + selected).distinct().forEach { item ->
                Row(Modifier.fillMaxWidth().clickable { onChange(if (item in selected) selected - item else selected + item) }) {
                    Checkbox(item in selected, { onChange(if (it) selected + item else selected - item) })
                    Text(item, Modifier.padding(top = 12.dp).weight(1f))
                }
            }
        }
    }, confirmButton = { TextButton(onClick = { show = false }) { Text("Concluir") } })
}
@Composable fun Goal(label: String, value: Double, target: Int) {
    Text("$label: " + "%.0f / %d".format(value, target))
    LinearProgressIndicator(progress = { (value / target).toFloat().coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth())
}
