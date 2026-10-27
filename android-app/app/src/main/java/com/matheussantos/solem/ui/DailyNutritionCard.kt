package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.domain.*
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable fun DailyNutritionCard(entries: List<HealthEntry>, available: Boolean, day: LocalDate, openMeals: () -> Unit) {
    val context=LocalContext.current
    val references=remember { runCatching {
        mealJson.decodeFromString<List<MealReference>>(context.assets.open("nutrition_catalog.json").bufferedReader().use { it.readText() })
    }.getOrNull() }
    val result=if(available && references!=null) dailyNutrition(entries,day,references) else null
    val known=result!=null && result.knownItems>0
    fun number(value: Double?)=if(known) String.format(Locale.forLanguageTag("pt-BR"),"%,.1f",value) else "—"
    Surface(shape=MaterialTheme.shapes.extraLarge,color=MaterialTheme.colorScheme.primaryContainer) {
        Column(Modifier.fillMaxWidth().padding(20.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
                Text("Nutrição de hoje",style=MaterialTheme.typography.titleLarge)
                Text(day.format(DateTimeFormatter.ofPattern("dd/MM")),style=MaterialTheme.typography.labelLarge)
            }
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                Column(Modifier.weight(1f)) {
                    Text("Calorias consumidas",style=MaterialTheme.typography.labelMedium)
                    Text(number(result?.calories),style=MaterialTheme.typography.headlineLarge,fontWeight=FontWeight.Bold)
                    Text("kcal",style=MaterialTheme.typography.bodyMedium)
                }
                Column(Modifier.weight(1f)) {
                    Text("Proteínas consumidas",style=MaterialTheme.typography.labelMedium)
                    Text(number(result?.protein),style=MaterialTheme.typography.headlineLarge,fontWeight=FontWeight.Bold)
                    Text("g",style=MaterialTheme.typography.bodyMedium)
                }
            }
            Text(when {
                result==null -> "Diário indisponível · abra Saúde para tentar novamente."
                result.meals==0 -> "Nenhuma refeição registrada hoje."
                !known -> "Sem cálculo ainda · informe pesos e referências em Saúde."
                result.partial -> "Total parcial · há alimentos ou refeições sem cálculo."
                else -> "${result.meals} refeição(ões) somadas automaticamente."
            },style=MaterialTheme.typography.bodyMedium)
            Text("Estimativas atualizadas ao salvar, editar ou remover refeições.",style=MaterialTheme.typography.bodySmall)
            TextButton(openMeals) { Text("Ver alimentação") }
        }
    }
}
