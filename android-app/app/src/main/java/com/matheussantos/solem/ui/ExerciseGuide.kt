package com.matheussantos.solem.ui

import android.provider.Settings
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.matheussantos.solem.domain.*
import kotlinx.coroutines.delay
import kotlinx.serialization.json.Json

/** Local vectors only: no account data, WebView, network request or autoplay. */
@Composable fun ExerciseGuide(exercise: String) {
    val context = LocalContext.current
    val catalog = remember {
        runCatching { context.assets.open("exercise_guides.json").bufferedReader().use {
            Json.decodeFromString<ExerciseGuides>(it.readText())
        } }.getOrNull()
    }
    if (catalog == null) {
        Text("Guia ilustrado indisponível nesta versão. O registro continua funcionando.", style=MaterialTheme.typography.bodySmall)
        return
    }
    val guide = catalog.forExercise(exercise)
    val motion = catalog.motions[guide.motion]
    val grip = catalog.grips[guide.grip]
    var expanded by remember(exercise) { mutableStateOf(false) }
    var frame by remember(exercise) { mutableIntStateOf(0) }
    var playing by remember(exercise) { mutableStateOf(false) }
    var reduced by remember { mutableStateOf(false) }
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    // Re-read the system preference whenever the app returns to the foreground.
    DisposableEffect(lifecycle, exercise) {
        fun motionPreference() {
            reduced = runCatching { Settings.Global.getFloat(context.contentResolver,
                Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f }.getOrDefault(false)
            if (reduced) playing = false
        }
        motionPreference()
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_PAUSE || event == Lifecycle.Event.ON_STOP) playing = false
            if (event == Lifecycle.Event.ON_RESUME) motionPreference()
        }
        lifecycle.addObserver(observer)
        onDispose { lifecycle.removeObserver(observer) }
    }
    LaunchedEffect(playing, expanded, exercise, reduced) {
        if (playing && expanded && !reduced && motion != null && motion.frames.size > 1) {
            frame = 0
            repeat(4) { delay(1500); frame = (it + 1) % 2 }
            playing = false
        }
    }
    val blend by animateFloatAsState(frame.toFloat(), tween(if(reduced) 0 else 220), label="guide pose")
    val uriHandler = LocalUriHandler.current
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement=Arrangement.spacedBy(10.dp)) {
            TextButton(onClick={ expanded = !expanded; playing = false }, modifier=Modifier.fillMaxWidth()) {
                Text(if(expanded) "Fechar guia · $exercise" else "Ver técnica e pegada · $exercise")
            }
            if(expanded) {
                if(grip != null) {
                    Text(grip.title, color=MaterialTheme.colorScheme.primary, style=MaterialTheme.typography.titleSmall)
                    Canvas(Modifier.fillMaxWidth().height(100.dp).semantics {contentDescription=grip.title+". "+grip.caption}) {
                        vectorArea(102f) {
                            polyline(listOf(listOf(35f,35f),listOf(265f,35f)),Color(0xFF607A95),9f)
                            grip.lines.forEach { polyline(it,Color(0xFFD3C6FF),4f) }
                            grip.marks.forEach { polyline(it,Color(0xFF91E0FF),2f) }
                        }
                    }
                    Text(grip.caption+" · vista de quem executa",style=MaterialTheme.typography.bodySmall)
                }
                if(motion != null) {
                    Text(guide.view, style=MaterialTheme.typography.labelMedium)
                    Canvas(Modifier.fillMaxWidth().height(230.dp).semantics {
                        contentDescription="$exercise: ${guide.labels.getOrNull(frame).orEmpty()}"
                    }) {
                        vectorArea(230f) {
                            polyline(listOf(listOf(25f,218f),listOf(275f,218f)),Color(0xFF29415B),1f)
                            motion.equipment.forEach {polyline(it,Color(0xFF607A95),4f)}
                            motion.circles.forEach { drawCircle(Color(0xFF607A95),it[2],Offset(it[0],it[1]),style=Stroke(3f)) }
                            motion.frames.forEachIndexed { index, pose ->
                                val alpha = if(motion.frames.size==1) 1f else if(index==0) 1f-blend else blend
                                pose.lines.forEachIndexed { n,line ->
                                    polyline(line,(if(n%2==0) Color(0xFFD3EDFF) else Color(0xFF88D7F3)).copy(alpha=alpha),7f)
                                }
                                drawCircle(Color(0xFFD3EDFF).copy(alpha=alpha),pose.head[2],Offset(pose.head[0],pose.head[1]))
                            }
                        }
                    }
                    Text(guide.labels.getOrNull(frame) ?: "Postura ilustrativa", style=MaterialTheme.typography.titleSmall)
                    if(motion.frames.size>1) {
                        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                            FilterChip(selected=frame==0,onClick={playing=false; frame=0},label={Text("Início")})
                            FilterChip(selected=frame==1,onClick={playing=false; frame=1},label={Text("Final")})
                        }
                        OutlinedButton(onClick={playing=!playing},enabled=!reduced,modifier=Modifier.fillMaxWidth()) {
                            Text(if(reduced) "Use Início / Final" else if(playing) "Parar animação" else "Reproduzir · 6 segundos")
                        }
                        Text("Duas posições ilustrativas, não um vídeo de execução.",style=MaterialTheme.typography.bodySmall)
                    }
                }
                guide.cues.forEach { Text("• $it",style=MaterialTheme.typography.bodyMedium) }
                Text(guide.avoid,color=MaterialTheme.colorScheme.onSurfaceVariant,style=MaterialTheme.typography.bodySmall)
                if(guide.source.startsWith("https://")) TextButton(onClick={uriHandler.openUri(guide.source)}) {Text("Referência de técnica ↗")}
                Text(catalog.notice,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

private fun DrawScope.vectorArea(height: Float, block: DrawScope.() -> Unit) {
    val factor = minOf(size.width/300f, size.height/height)
    withTransform({translate((size.width-300f*factor)/2f,0f);scale(factor,factor,pivot=Offset.Zero)},block)
}
private fun DrawScope.polyline(points: List<List<Float>>, color: Color, width: Float) {
    points.zipWithNext().forEach { (a,b) ->
        drawLine(color,Offset(a[0],a[1]),Offset(b[0],b[1]),width,StrokeCap.Round)
    }
}
