package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.serialization.json.*
import java.time.LocalDate
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.util.Locale

private fun amount(value: Double) = String.format(Locale.getDefault(), "%.1f", value)
@Composable fun MealReferenceDetails(references: List<MealReference>) {
    var expanded by remember { mutableStateOf(false) }
    TextButton(onClick={expanded=!expanded}) { Text(if(expanded) "Ocultar referências e preparo" else "Referências nutricionais e preparo") }
    if(expanded) {
        Text("Nomes simplificados; cálculos pelas referências abaixo. Preparo e ingredientes podem mudar os valores.",style=MaterialTheme.typography.bodySmall)
        references.forEach { Text("${it.displayName} — ${it.name}",style=MaterialTheme.typography.bodySmall) }
    }
}
@Composable fun MealNutritionSummary(estimate: MealEstimate) {
    Text(if(estimate.complete) "Estimativa nutricional" else "Estimativa parcial",style=MaterialTheme.typography.titleMedium)
    val values=estimate.totals
    Text("≈ ${amount(values.kcal)} kcal · proteínas ${amount(values.protein)} g · carboidratos ${amount(values.carbs)} g")
    Text("Gorduras ${amount(values.fat)} g · fibras ${amount(values.fiber)} g")
    if(estimate.missing>0) Text("${estimate.missing} alimento(s) não calculados. Sem correspondência ou porção não significa zero calorias.",
        color=MaterialTheme.colorScheme.error)
    Text("Cálculo pelo peso informado e pela referência nutricional. Óleo, molhos e preparo podem alterar os valores.",style=MaterialTheme.typography.bodySmall)
}

@Composable fun MealReview(day: LocalDate, catalog: Catalog, workspace: WorkspaceViewModel,
    references: List<MealReference>, initial: List<MealFood>, busy: Boolean,
    previous: HealthEntry?=null, saved: () -> Unit={}, weighed: Boolean=false) {
    key(day, previous?.id) {
        var spoken by remember { mutableStateOf<VoiceDraft?>(null) }
        var revision by remember { mutableStateOf(0) }
        if(previous == null) VoiceInput("Almoço, arroz 170, feijão 323, ovo cozido 371, peso acumulado.", busy,
            parse={parseMealVoice(it,references)}, apply={spoken=it;revision++})
        key(revision) {
            MealDraftReview(day,catalog,workspace,references,spoken?.items ?: initial,busy,previous,
                saved={if(previous==null){spoken=null;revision++};saved()},weighed=weighed,spoken=spoken)
        }
    }
}

@Composable private fun MealDraftReview(day: LocalDate, catalog: Catalog, workspace: WorkspaceViewModel,
    references: List<MealReference>, initial: List<MealFood>, busy: Boolean,
    previous: HealthEntry?, saved: () -> Unit, weighed: Boolean, spoken: VoiceDraft?) {
    var mode by rememberSaveable(previous?.id) {mutableStateOf(if(spoken?.cumulative ?: defaultCumulativeMeal(previous?.details)) "Peso acumulado da balança" else "Peso individual de cada alimento")}
    Choice("Como vai informar os pesos?",mode,listOf("Peso individual de cada alimento","Peso acumulado da balança")) {mode=it}
    Text("Os modos têm rascunhos separados. Salve antes de trocar de modo para manter alterações.",style=MaterialTheme.typography.bodySmall)
    if(mode=="Peso acumulado da balança") {
        CumulativeMealReview(day,catalog,workspace,references,initial,busy,previous,saved,spoken)
        return
    }
    var items by remember { mutableStateOf(initial) }
    var kind by rememberSaveable { mutableStateOf(spoken?.mealType ?: previous?.text("tipo_refeicao") ?: "Almoço") }
    var time by rememberSaveable { mutableStateOf(previous?.loggedAt ?: LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"))) }
    var confirmed by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val links=LocalUriHandler.current
    MealReferenceDetails(references)
    Text(if(weighed) "Refeição com balança" else "Confira seu prato",style=MaterialTheme.typography.titleLarge)
    Text("Zere a balança com o prato vazio (tara). Pese só a parte consumida de cada alimento. Escolha o mesmo preparo: cru ou cozido. Inclua óleo e molhos. Use 0 g para deixar sem cálculo.")
    items.forEachIndexed { index,item ->
        key(items.size,index) { Panel(foodDisplayName(item.name,references).ifBlank { "Alimento" }) {
            Field("Alimento",foodDisplayName(item.name,references)) { name -> items=items.mapIndexed { at,food -> if(at==index) food.copy(name=name.take(80)) else food }; confirmed=false }
            val options=listOf("Sem correspondência — não calcular")+references.map { it.displayName }
            val selected=references.firstOrNull { it.id==item.foodId }?.displayName ?: options.first()
            Choice("Referência nutricional / preparo",selected,options) { choice ->
                val reference=references.firstOrNull { it.displayName==choice }
                val id=reference?.id.orEmpty()
                items=items.mapIndexed { at,food -> if(at==index) food.copy(foodId=id, name=if(food.name=="Outro alimento") reference?.name ?: choice else food.name) else food }; confirmed=false
            }
            var gramsText by remember { mutableStateOf(amount(item.grams)) }
            Field("Peso consumido (g)",gramsText,true) { value ->
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
            runCatching { calculateMeal(listOf(item),references) }.getOrNull()?.let { portion ->
                if(portion.complete) Text("Este alimento: ${amount(portion.totals.kcal)} kcal · ${amount(portion.totals.protein)} g de proteína")
                else Text("Sem cálculo: informe peso e referência compatível.")
            }
        } }
    }
    TextButton(onClick={items=items+MealFood("Outro alimento");confirmed=false},enabled=items.size<12) { Text("Adicionar alimento") }
    Text("Sem referência compatível? Use o registro simples; não substitua por outro alimento.",style=MaterialTheme.typography.bodySmall)
    val estimate=runCatching { calculateMeal(items,references) }
    estimate.getOrNull()?.let { Text("Total da refeição · soma dos alimentos"); MealNutritionSummary(it) }
    estimate.exceptionOrNull()?.let { Text(it.message.orEmpty(),color=MaterialTheme.colorScheme.error) }
    Choice("Refeição",kind,(catalog.mealTypes+kind).distinct()) {kind=it}
    Field("Horário (HH:MM:SS)",time) {time=it}
    Row { Checkbox(checked=confirmed,onCheckedChange={confirmed=it}); Text("Revisei os alimentos e entendo que os valores são estimativas.") }
    error?.let { Text(it,color=MaterialTheme.colorScheme.error) }
    Button(onClick={
        try {
            val checked=LocalTime.parse(time).format(DateTimeFormatter.ofPattern("HH:mm:ss"))
            val details=photoMealDetails(kind,items,references,weighed || previous?.text("input_method")=="weighed")
            workspace.saveHealth(day.toString(),checked,"meal",details,previous?.id,onSaved={
                if(previous==null) {items=emptyList();confirmed=false}; saved()
            })
        } catch(e: Exception) { error=e.message ?: "Confira o horário e as porções." }
    },enabled=!busy && confirmed && estimate.isSuccess) { Text(if(previous==null) "Confirmar e salvar refeição" else "Salvar edição nutricional") }
}
