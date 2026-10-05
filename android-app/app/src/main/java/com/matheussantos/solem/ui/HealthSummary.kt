package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.ui.theme.LocalDashboardPreferences
import java.util.Locale

@Composable fun HealthSummary(rows:List<HealthEntry>,available:Boolean,busy:Boolean,select:(Int)->Unit,addWater:(Int)->Unit) {
    val settings=LocalDashboardPreferences.current
    val water=rows.filter {it.kind=="water"}.sumOf {entry ->
        val volume=entry.number("volume_ml");val count=entry.number("quantidade")
        if(volume.isFinite() && count.isFinite() && volume in 50.0..5000.0 && count in 1.0..50.0) volume*count else 0.0
    }
    val weight=rows.firstOrNull {it.kind=="weight"}?.number("kg")?.takeIf {it.isFinite() && it>0}
    val sleep=rows.firstOrNull {it.kind=="sleep"}?.number("duracao_min")?.takeIf {it.isFinite() && it>0}
    Surface(shape=MaterialTheme.shapes.extraLarge,color=MaterialTheme.colorScheme.surfaceContainer) {
        Column(Modifier.fillMaxWidth().padding(20.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(18.dp)) {
                JourneyRing((water/settings.waterMl).toFloat(),if(available) "${(water/settings.waterMl*100).toInt().coerceAtMost(100)}%" else "—","hidratação")
                Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(6.dp)) {
                    Text("Um cuidado por vez",style=MaterialTheme.typography.titleLarge)
                    Text(if(available) "${String.format(Locale.forLanguageTag("pt-BR"),"%.1f",water/1000)} / ${String.format(Locale.forLanguageTag("pt-BR"),"%.1f",settings.waterMl/1000.0)} L" else "Aguardando diário",
                        style=MaterialTheme.typography.titleMedium,color=MaterialTheme.colorScheme.primary)
                    Text("A meta é pessoal e pode ser ajustada.",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            Text("Registrar água",style=MaterialTheme.typography.labelLarge)
            Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                listOf(250,500,750).forEach {volume ->
                    FilledTonalButton({addWater(volume)},enabled=!busy && available,modifier=Modifier.weight(1f),contentPadding=PaddingValues(horizontal=6.dp,vertical=12.dp)) {
                        Text("+$volume ml",style=MaterialTheme.typography.labelLarge)
                    }
                }
            }
            Text("Cada toque salva um registro individual no dia selecionado.",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
    Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
        HealthTile("Refeições",if(available) "${rows.count {it.kind=="meal"}}" else "—","Abrir alimentação",Icons.Outlined.Restaurant,Modifier.weight(1f)) {select(0)}
        HealthTile("Sono",sleep?.let {"${it.toInt()/60}h ${it.toInt()%60}m"} ?: "—","Registrar descanso",Icons.Outlined.Bedtime,Modifier.weight(1f)) {select(3)}
    }
    Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
        HealthTile("Peso",weight?.let {String.format(Locale.forLanguageTag("pt-BR"),"%.1f kg",it)} ?: "—","Seu histórico",Icons.Outlined.MonitorWeight,Modifier.weight(1f)) {select(2)}
        HealthTile("Fotos","Sua evolução","Rosto e corpo",Icons.Outlined.PhotoCamera,Modifier.weight(1f)) {select(4)}
    }
    Text("Seu diário é privado. Peso e fotos não aumentam XP. Valores ausentes ficam em branco, sem avaliações do corpo.",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
}

@Composable private fun HealthTile(title:String,value:String,caption:String,icon:ImageVector,modifier:Modifier,onClick:()->Unit) {
    Surface(onClick=onClick,modifier=modifier,shape=MaterialTheme.shapes.large,color=MaterialTheme.colorScheme.surfaceContainer) {
        Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
            Icon(icon,null,tint=MaterialTheme.colorScheme.primary)
            Text(title,style=MaterialTheme.typography.labelLarge,color=MaterialTheme.colorScheme.onSurfaceVariant)
            Text(value,style=MaterialTheme.typography.titleLarge)
            Text(caption,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.primary)
        }
    }
}
