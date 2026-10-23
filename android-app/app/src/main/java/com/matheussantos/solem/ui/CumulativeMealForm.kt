package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.serialization.json.decodeFromJsonElement
import java.time.LocalDate
import java.time.LocalTime
import java.time.format.DateTimeFormatter
import java.util.Locale

private fun scaleNumber(value:Double)=String.format(Locale.getDefault(),"%.1f",value)
private fun parseScale(value:String)=value.replace(',','.').toDoubleOrNull() ?: Double.NaN

@Composable fun CumulativeMealReview(day:LocalDate,catalog:Catalog,workspace:WorkspaceViewModel,
    references:List<MealReference>,initial:List<MealFood>,busy:Boolean,previous:HealthEntry?,saved:()->Unit) {
    val stored=remember {runCatching {previous?.details?.get("weighing")?.let {mealJson.decodeFromJsonElement<MealWeighing>(it)}}.getOrNull()}
    var items by remember {mutableStateOf(initial)}
    var baseline by rememberSaveable {mutableStateOf(scaleNumber(stored?.baseline ?: 0.0))}
    var readings by remember {mutableStateOf(stored?.readings?.takeIf {it.size==initial.size}?.map(::scaleNumber)
        ?: initial.runningFold(0.0) {sum,item ->sum+item.grams}.drop(1).map(::scaleNumber))}
    var kind by rememberSaveable {mutableStateOf(previous?.text("tipo_refeicao") ?: "Almoço")}
    var time by rememberSaveable {mutableStateOf(previous?.loggedAt ?: LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")))}
    var confirmed by remember {mutableStateOf(false)}
    var error by remember {mutableStateOf<String?>(null)}
    Text("Balança · peso acumulado",style=MaterialTheme.typography.titleLarge)
    Text("Coloque os alimentos na ordem do registro, sem zerar a balança entre eles. Informe 0 como peso inicial se usou tara. Se retirou comida ou zerou novamente, use o modo individual.")
    Field("Leitura inicial: prato vazio (g)",baseline,true) {baseline=it;confirmed=false}
    items.forEachIndexed {index,item ->
        Panel("${index+1}. ${item.name}") {
            Field("Alimento",item.name) {name ->items=items.mapIndexed {at,food->if(at==index)food.copy(name=name.take(80))else food};confirmed=false}
            val options=listOf("Sem correspondência — não calcular")+references.map {it.name}
            val current=references.firstOrNull {it.id==item.foodId}?.name ?: options.first()
            Choice("Referência nutricional / preparo",current,options) {choice ->
                val id=references.firstOrNull {it.name==choice}?.id.orEmpty()
                items=items.mapIndexed {at,food->if(at==index)food.copy(foodId=id,name=if(food.name=="Outro alimento")choice else food.name)else food};confirmed=false
            }
            Field("Leitura da balança após este alimento (g)",readings[index],true) {value ->readings=readings.mapIndexed {at,text->if(at==index)value else text};confirmed=false}
            runCatching {cumulativeMealItems(items.take(index+1),MealWeighing(baseline=parseScale(baseline),readings=readings.take(index+1).map(::parseScale)))}.getOrNull()?.lastOrNull()?.let {food ->
                val before=if(index==0)parseScale(baseline)else parseScale(readings[index-1])
                Text("${readings[index]} − ${scaleNumber(before)} = ${scaleNumber(food.grams)} g deste alimento")
                runCatching {calculateMeal(listOf(food),references)}.getOrNull()?.takeIf {it.complete}?.let {
                    Text("${scaleNumber(it.totals.kcal)} kcal · ${scaleNumber(it.totals.protein)} g de proteína")
                }
            }
            if(index==items.lastIndex) TextButton({items=items.dropLast(1);readings=readings.dropLast(1);confirmed=false},enabled=!busy) {Text("Remover última adição")}
        }
    }
    TextButton({items=items+MealFood("Outro alimento");readings=readings+"";confirmed=false},enabled=!busy && items.size<12) {Text("Adicionar próximo alimento")}
    Text("Remova adições do fim para o começo para não juntar pesos de alimentos diferentes. Para outras exclusões, use o modo individual.",style=MaterialTheme.typography.bodySmall)
    val weighing=MealWeighing(baseline=parseScale(baseline),readings=readings.map(::parseScale))
    val estimate=runCatching {calculateMeal(cumulativeMealItems(items,weighing),references)}
    estimate.getOrNull()?.let {Text("Total da refeição · sem o prato");MealNutritionSummary(it)}
    estimate.exceptionOrNull()?.let {Text(it.message.orEmpty(),color=MaterialTheme.colorScheme.error)}
    Choice("Refeição",kind,(catalog.mealTypes+kind).distinct()) {kind=it}
    Field("Horário (HH:MM:SS)",time) {time=it}
    Row {Checkbox(confirmed,{confirmed=it});Text("Conferi a ordem, as leituras e os pesos calculados.")}
    error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
    Button({try {
        val checked=LocalTime.parse(time).format(DateTimeFormatter.ofPattern("HH:mm:ss"))
        val details=photoMealDetails(kind,items,references,true,weighing)
        workspace.saveHealth(day.toString(),checked,"meal",details,previous?.id,onSaved={if(previous==null){items=emptyList();readings=emptyList();confirmed=false};saved()})
    } catch(e:Exception){error=e.message ?: "Confira as leituras."}},enabled=!busy && confirmed && estimate.isSuccess) {Text(if(previous==null) "Confirmar e salvar refeição" else "Salvar edição nutricional")}
}
