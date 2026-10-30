package com.matheussantos.solem.ui

import android.provider.Settings
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeJoin
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
    var position by remember(exercise) { mutableFloatStateOf(0f) }
    var playing by remember(exercise) { mutableStateOf(false) }
    var reduced by remember { mutableStateOf(false) }
    val appMotion = com.matheussantos.solem.ui.theme.LocalDashboardPreferences.current.motion
    val lifecycle = LocalLifecycleOwner.current.lifecycle
    // Re-read the system preference whenever the app returns to the foreground.
    DisposableEffect(lifecycle, exercise, appMotion) {
        fun motionPreference() {
            reduced = !appMotion || runCatching { Settings.Global.getFloat(context.contentResolver,
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
            val start = withFrameNanos { it }
            var lastPaint = start - 34_000_000L
            while(true) {
                val now = withFrameNanos { it }
                val elapsed = (now-start)/1_000_000L
                if(now-lastPaint>=33_333_333L || elapsed>=8000L) {
                    position=guidePhase(elapsed); lastPaint=now
                }
                if(elapsed>=8000L) break
            }
            position=0f
            playing = false
        }
    }
    val uriHandler = LocalUriHandler.current
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement=Arrangement.spacedBy(10.dp)) {
            TextButton(onClick={ expanded = !expanded; playing = false }, modifier=Modifier.fillMaxWidth()) {
                Text(if(expanded) "Fechar guia · $exercise" else "Ver execução e pegada · $exercise")
            }
            if(expanded) {
                if(grip != null) {
                    Text("Pegada ${grip.title.lowercase()}", color=MaterialTheme.colorScheme.primary, style=MaterialTheme.typography.titleMedium)
                    Text(grip.instruction,style=MaterialTheme.typography.bodyMedium)
                    Canvas(Modifier.fillMaxWidth().height(155.dp).semantics {contentDescription=grip.title+". "+grip.caption}) {
                        vectorArea(360f,165f) {
                            grip.shapes.forEach { drawVector(it.shape,it.coords) }
                        }
                    }
                    Text(grip.caption+" · vista de quem executa",style=MaterialTheme.typography.bodySmall)
                }
                if(motion != null) {
                    Text(guide.view, style=MaterialTheme.typography.labelMedium)
                    Canvas(Modifier.fillMaxWidth().aspectRatio(1f).semantics {
                        contentDescription="$exercise: ${motion.direction}"
                    }) {
                        vectorArea(440f,440f) {
                            motion.static.forEach { drawVector(it.shape,it.coords) }
                            motion.sample(position).forEachIndexed { i,coords -> drawVector(motion.shapes[i],coords) }
                        }
                    }
                    Text(motion.direction, style=MaterialTheme.typography.titleSmall)
                    if(motion.frames.size>1) {
                        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                            FilterChip(selected=position<.02f,onClick={playing=false; position=0f},label={Text("Início")})
                            FilterChip(selected=kotlin.math.abs(position-.5f)<.02f,onClick={playing=false; position=.5f},label={Text("Meio")})
                            FilterChip(selected=position>.98f,onClick={playing=false; position=1f},label={Text("Final")})
                        }
                        Text("Explore o movimento",style=MaterialTheme.typography.labelMedium)
                        Slider(value=position,onValueChange={playing=false;position=it},modifier=Modifier.semantics {contentDescription="Posição do movimento"})
                        OutlinedButton(onClick={playing=!playing},enabled=!reduced,modifier=Modifier.fillMaxWidth()) {
                            Text(if(reduced) "Use os controles de posição" else if(playing) "Pausar movimento" else "Reproduzir movimento · 8 s")
                        }
                        Text("Movimento ilustrativo contínuo · 2 ciclos",style=MaterialTheme.typography.bodySmall)
                    }
                }
                guide.cues.forEach { Text("• $it",style=MaterialTheme.typography.bodyMedium) }
                motion?.landmarks?.forEach { Text(it,style=MaterialTheme.typography.labelMedium,color=MaterialTheme.colorScheme.primary) }
                Text(guide.avoid,color=MaterialTheme.colorScheme.onSurfaceVariant,style=MaterialTheme.typography.bodySmall)
                if(guide.source.startsWith("https://")) TextButton(onClick={uriHandler.openUri(guide.source)}) {Text("Referência de técnica ↗")}
                Text(catalog.notice,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

private fun DrawScope.vectorArea(width: Float, height: Float, block: DrawScope.() -> Unit) {
    val factor = minOf(size.width/width, size.height/height)
    withTransform({translate((size.width-width*factor)/2f,0f);scale(factor,factor,pivot=Offset.Zero)},block)
}
private fun DrawScope.drawVector(shape: GuideShape, coords: List<Float>) {
    val fill=shape.fill.takeIf {it.isNotBlank()}?.let {Color(android.graphics.Color.parseColor(it))}
    val stroke=shape.stroke.takeIf {it.isNotBlank()}?.let {Color(android.graphics.Color.parseColor(it))}
    if(shape.kind=="ellipse") {
        val top=Offset(coords[0]-coords[2],coords[1]-coords[3]);val dimensions=Size(coords[2]*2,coords[3]*2)
        if(fill!=null)drawOval(fill,top,dimensions)
        if(stroke!=null)drawOval(stroke,top,dimensions,style=Stroke(shape.width))
    } else {
        val path=Path();var index=0
        fun next()=coords[index++]
        shape.commands.forEach {command->when(command) {
            'M'->path.moveTo(next(),next())
            'L'->path.lineTo(next(),next())
            'Q'->path.quadraticTo(next(),next(),next(),next())
            'C'->path.cubicTo(next(),next(),next(),next(),next(),next())
            'Z'->path.close()
        }}
        if(fill!=null)drawPath(path,fill)
        if(stroke!=null)drawPath(path,stroke,style=Stroke(shape.width,cap=StrokeCap.Round,join=StrokeJoin.Round))
    }
}
