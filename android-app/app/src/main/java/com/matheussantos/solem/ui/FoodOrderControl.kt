package com.matheussantos.solem.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.CustomAccessibilityAction
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.customActions
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.zIndex
import kotlin.math.roundToInt

@Composable fun FoodOrderControl(names: List<String>, enabled: Boolean, move: (Int, Int) -> Unit) {
    if (names.size < 2) return
    val latestMove by rememberUpdatedState(move)
    val step = with(LocalDensity.current) { 62.dp.toPx() }
    var dragging by remember { mutableStateOf(-1) }
    var distance by remember { mutableFloatStateOf(0f) }
    val target = if (dragging >= 0) (dragging + (distance / step).roundToInt()).coerceIn(names.indices) else -1
    Text("Ordem dos alimentos", style = MaterialTheme.typography.titleMedium)
    Text("Arraste pela alça ⋮⋮ ou use as setas. As leituras ficam na mesma posição; confira os novos pesos antes de salvar.", style = MaterialTheme.typography.bodySmall)
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        names.forEachIndexed { index, name ->
            val active = dragging == index
            val shape = RoundedCornerShape(10.dp)
            Row(Modifier.fillMaxWidth().height(56.dp).zIndex(if (active) 1f else 0f)
                .graphicsLayer { translationY = if (active) distance else 0f }
                .background(MaterialTheme.colorScheme.surfaceContainer, shape)
                .border(1.dp, if (target == index || active) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant, shape),
                verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(48.dp).semantics {
                    contentDescription = "Mover $name"
                    customActions = listOfNotNull(
                        if (enabled && index > 0) CustomAccessibilityAction("Subir") { latestMove(index,index-1);true } else null,
                        if (enabled && index < names.lastIndex) CustomAccessibilityAction("Descer") { latestMove(index,index+1);true } else null)
                }.pointerInput(names, enabled) {
                    if (enabled) detectVerticalDragGestures(
                        onDragStart = { dragging=index;distance=0f },
                        onDragCancel = { dragging=-1;distance=0f },
                        onDragEnd = {
                            val destination=(index+(distance/step).roundToInt()).coerceIn(names.indices)
                            dragging=-1;distance=0f
                            if(destination!=index)latestMove(index,destination)
                        }) { change, delta -> change.consume();distance=(distance+delta).coerceIn(-index*step,(names.lastIndex-index)*step) }
                }, contentAlignment=Alignment.Center) { Text("⋮⋮",style=MaterialTheme.typography.titleLarge) }
                Text("${index+1}. $name",Modifier.weight(1f),maxLines=2,overflow=TextOverflow.Ellipsis)
                IconButton({ latestMove(index,index-1) },enabled=enabled && index>0,
                    modifier=Modifier.semantics { contentDescription="Subir $name" }) { Text("↑") }
                IconButton({ latestMove(index,index+1) },enabled=enabled && index<names.lastIndex,
                    modifier=Modifier.semantics { contentDescription="Descer $name" }) { Text("↓") }
            }
        }
    }
}
