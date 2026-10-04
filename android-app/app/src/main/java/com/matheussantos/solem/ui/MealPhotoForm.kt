package com.matheussantos.solem.ui

import android.app.Application
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.*
import kotlinx.serialization.json.*
import java.time.LocalDate
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.util.Locale

private fun amount(value: Double) = String.format(Locale.getDefault(), "%.1f", value)
@Composable fun MealNutritionSummary(estimate: MealEstimate) {
    Text(if(estimate.complete) "Estimativa nutricional" else "Estimativa parcial",style=MaterialTheme.typography.titleMedium)
    val values=estimate.totals
    Text("≈ ${amount(values.kcal)} kcal · proteínas ${amount(values.protein)} g · carboidratos ${amount(values.carbs)} g")
    Text("Gorduras ${amount(values.fat)} g · fibras ${amount(values.fiber)} g")
    if(estimate.missing>0) Text("${estimate.missing} alimento(s) não calculados. Sem correspondência ou porção não significa zero calorias.",
        color=MaterialTheme.colorScheme.error)
    Text("Porções aproximadas, não medidas. Óleo, molhos e preparo podem alterar os valores.",style=MaterialTheme.typography.bodySmall)
}

@Composable fun MealPhotoForm(day: LocalDate, catalog: Catalog, workspace: WorkspaceViewModel, busy: Boolean) {
    val account by workspace.state.collectAsStateWithLifecycle()
    val application=LocalContext.current.applicationContext as Application
    val vm: MealAnalysisViewModel=viewModel(key="meal-photo-${account.accountId}", factory=object: androidx.lifecycle.ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST") override fun <T: androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
            MealAnalysisViewModel(application,workspace.trainingClient) as T
    })
    val state by vm.state.collectAsStateWithLifecycle()
    var open by rememberSaveable { mutableStateOf(false) }
    var consent by remember(day) { mutableStateOf(false) }
    var adult by remember(day) { mutableStateOf(false) }
    val links=LocalUriHandler.current
    val picker=rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { vm.select(it) }
    LaunchedEffect(day) { vm.clear() }
    DisposableEffect(vm) { onDispose { vm.clear() } }
    TextButton(onClick={ open=!open }) { Text(if(open) "Fechar registro por foto" else "Registrar refeição por foto") }
    if(open) Panel("Foto do prato · Gemini via OpenRouter") {
        Text("A foto será enviada ao OpenRouter e ao Google Vertex. O roteamento exige endpoint sem retenção (ZDR), mas os serviços processam a imagem e metadados conforme suas políticas. Não envie rostos, documentos ou dados pessoais.")
        Text("Só alimentos e valores confirmados são salvos no diário, não a foto. Teto de US$ 1/mês para todo o app, com saldo do administrador. Até 6 tentativas/conta/dia e 20/app/dia; sem recarga ou troca automática de modelo.",style=MaterialTheme.typography.bodySmall)
        TextButton(onClick={ links.openUri("https://openrouter.ai/privacy") }) { Text("Privacidade do OpenRouter") }
        Button(onClick={ picker.launch(arrayOf("image/jpeg","image/png","image/webp")) },enabled=!state.busy && !busy) {
            Text(if(state.source==null) "Escolher foto do prato" else "Trocar foto do prato")
        }
        if(state.source!=null) Text("Foto selecionada. Metadados de localização serão removidos antes do envio.")
        Row { Checkbox(checked=consent,onCheckedChange={consent=it}); Text("Autorizo enviar somente esta foto do prato ao OpenRouter e ao Google e li o aviso acima.") }
        Row { Checkbox(checked=adult,onCheckedChange={adult=it}); Text("Tenho 18 anos ou mais.") }
        Button(onClick={vm.analyze(consent,adult)},enabled=consent && adult && state.source!=null && !state.busy && !busy) {
            Text("Analisar foto")
        }
        if(state.busy) { LinearProgressIndicator(Modifier.fillMaxWidth()); Text("Identificando alimentos e sugerindo porções…") }
        state.message?.let { Text(it,color=MaterialTheme.colorScheme.error) }
        state.draft?.let { draft ->
            key(day,state.revision) {
                MealReview(day,catalog,workspace,vm.catalog,draft.items,busy,
                    saved={vm.clear()})
            }
            TextButton(onClick=vm::clear,enabled=!state.busy) { Text("Descartar sugestão") }
        }
    }
}

@Composable fun MealReview(day: LocalDate, catalog: Catalog, workspace: WorkspaceViewModel,
    references: List<MealReference>, initial: List<MealFood>, busy: Boolean,
    previous: HealthEntry?=null, saved: () -> Unit={}) {
    var items by remember { mutableStateOf(initial) }
    var kind by rememberSaveable { mutableStateOf(previous?.text("tipo_refeicao") ?: "Almoço") }
    var time by rememberSaveable { mutableStateOf(previous?.loggedAt ?: LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"))) }
    var confirmed by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val links=LocalUriHandler.current
    Text("Confira seu prato",style=MaterialTheme.typography.titleLarge)
    Text("A foto não mede o peso. Confira preparo e porção. Use 0 g quando não souber estimar.")
    items.forEachIndexed { index,item ->
        key(items.size,index) { Panel(item.name.ifBlank { "Alimento" }) {
            Field("Alimento",item.name) { name -> items=items.mapIndexed { at,food -> if(at==index) food.copy(name=name.take(80)) else food }; confirmed=false }
            val options=listOf("Sem correspondência — não calcular")+references.map { it.name }
            val selected=references.firstOrNull { it.id==item.foodId }?.name ?: options.first()
            Choice("Referência nutricional / preparo",selected,options) { choice ->
                val id=references.firstOrNull { it.name==choice }?.id.orEmpty()
                items=items.mapIndexed { at,food -> if(at==index) food.copy(foodId=id) else food }; confirmed=false
            }
            var gramsText by remember { mutableStateOf(amount(item.grams)) }
            Field("Porção estimada (g)",gramsText,true) { value ->
                gramsText=value
                val grams=value.replace(',','.').toDoubleOrNull() ?: Double.NaN
                items=items.mapIndexed { at,food -> if(at==index) food.copy(grams=grams) else food }; confirmed=false
            }
            Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                listOf(0.5,1.5).forEach { factor -> TextButton(onClick={
                    val grams=(item.grams*factor).takeIf { it.isFinite() }?.coerceIn(0.0,2000.0) ?: 0.0
                    gramsText=amount(grams)
                    items=items.mapIndexed { at,food -> if(at==index) food.copy(grams=grams) else food }; confirmed=false
                }) { Text(if(factor==0.5) "Metade" else "+50%") } }
                TextButton(onClick={items=items.filterIndexed { at,_ -> at!=index };confirmed=false}) { Text("Remover") }
            }
            references.firstOrNull { it.id==item.foodId }?.let { reference ->
                TextButton(onClick={ links.openUri(reference.sourceUrl) }) { Text("Consultar fonte USDA") }
            }
            Text("Identificação sugerida: "+when(item.confidence) { "high"->"mais provável"; "medium"->"incerta"; else->"confira com atenção" },style=MaterialTheme.typography.bodySmall)
        } }
    }
    TextButton(onClick={items=items+MealFood("Outro alimento");confirmed=false},enabled=items.size<12) { Text("Adicionar alimento que faltou") }
    val estimate=runCatching { calculateMeal(items,references) }
    estimate.getOrNull()?.let { MealNutritionSummary(it) }
    estimate.exceptionOrNull()?.let { Text(it.message.orEmpty(),color=MaterialTheme.colorScheme.error) }
    Choice("Refeição",kind,(catalog.mealTypes+kind).distinct()) {kind=it}
    Field("Horário (HH:MM:SS)",time) {time=it}
    Row { Checkbox(checked=confirmed,onCheckedChange={confirmed=it}); Text("Revisei os alimentos e entendo que os valores são estimativas.") }
    error?.let { Text(it,color=MaterialTheme.colorScheme.error) }
    Button(onClick={
        try {
            val checked=LocalTime.parse(time).format(DateTimeFormatter.ofPattern("HH:mm:ss"))
            val details=photoMealDetails(kind,items,references)
            workspace.saveHealth(day.toString(),checked,"meal",details,previous?.id,onSaved=saved)
        } catch(e: Exception) { error=e.message ?: "Confira o horário e as porções." }
    },enabled=!busy && confirmed && estimate.isSuccess) { Text(if(previous==null) "Confirmar e salvar refeição" else "Salvar edição nutricional") }
}
