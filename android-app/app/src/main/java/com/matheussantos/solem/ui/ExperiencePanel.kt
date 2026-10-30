package com.matheussantos.solem.ui

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.media.MediaPlayer
import android.widget.VideoView
import android.widget.MediaController
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.ui.theme.LocalDashboardPreferences
import org.json.JSONArray
import org.json.JSONObject
import java.time.format.DateTimeFormatter

@Composable fun WelcomeGuide(navigate:(Int)->Unit) {
    val context=LocalContext.current
    val owner=LocalGpsAccount.current
    val prefs=remember(owner) {context.getSharedPreferences("solem_guide_$owner",Context.MODE_PRIVATE)}
    var expanded by rememberSaveable(owner) {mutableStateOf(!prefs.getBoolean("done",false))}
    var step by rememberSaveable(owner) {mutableIntStateOf(0)}
    val motion=LocalDashboardPreferences.current.motion
    val bob=remember {Animatable(0f)}
    LaunchedEffect(step,motion) {
        bob.snapTo(0f)
        if(motion && step>0) {bob.animateTo(-5f,tween(350));bob.animateTo(0f,tween(450))}
    }
    val steps=listOf(
        Triple("Seu ponto de partida","Na Jornada, veja suas missões, seu nível e os registros do dia. Cada atividade salva constrói seu histórico.",0),
        Triple("Um treino, um registro","Escolha o exercício, confira a técnica e use cronômetro ou GPS. Cada sessão pode ser editada separadamente.",1),
        Triple("Cuide da rotina inteira","Em Saúde, registre refeições, água, peso e sono. A balança acumulada calcula cada porção pela diferença.",3),
        Triple("Veja o que mudou","Em Evolução física, compare seus treinos ao longo do tempo. Descanso não retira seus pontos.",2),
        Triple("Seu ritmo, suas escolhas","Em Personalizar, ajuste metas, tema, contraste, tamanho do texto e movimento. Comece com o que cabe no seu dia.",17))
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            TextButton({expanded=!expanded},modifier=Modifier.fillMaxWidth()) {Text(if(expanded) "Recolher guia rápido" else "Conheça seu Solem · guia rápido")}
            if(expanded) {
                val accent=MaterialTheme.colorScheme.primary
                val skin=MaterialTheme.colorScheme.onSurface
                Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(16.dp)) {
                    Canvas(Modifier.size(64.dp,88.dp).graphicsLayer {translationY=bob.value}) {
                        val w=size.width;val h=size.height
                        drawCircle(skin,w*.17f,Offset(w*.5f,h*.2f))
                        drawLine(accent,Offset(w*.5f,h*.42f),Offset(w*.5f,h*.70f),w*.35f,StrokeCap.Round)
                        drawLine(skin,Offset(w*.35f,h*.46f),Offset(w*.18f,h*.64f),w*.09f,StrokeCap.Round)
                        drawLine(skin,Offset(w*.65f,h*.46f),Offset(w*.82f,h*.30f),w*.09f,StrokeCap.Round)
                        drawLine(skin,Offset(w*.40f,h*.72f),Offset(w*.35f,h*.94f),w*.11f,StrokeCap.Round)
                        drawLine(skin,Offset(w*.60f,h*.72f),Offset(w*.65f,h*.94f),w*.11f,StrokeCap.Round)
                    }
                    Column(Modifier.weight(1f)) {
                        Text("GUIA · ${step+1} DE 5",style=MaterialTheme.typography.labelSmall,color=accent)
                        Text(steps[step].first,style=MaterialTheme.typography.titleLarge)
                    }
                }
                Text(steps[step].second)
                Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                    OutlinedButton({step--},enabled=step>0,modifier=Modifier.weight(1f)) {Text("Anterior")}
                    Button({step=(step+1)%5},modifier=Modifier.weight(1f)) {Text(if(step==4) "Rever" else "Próximo")}
                }
                TextButton({navigate(steps[step].third)}) {Text("Abrir esta área")}
                TextButton({prefs.edit().putBoolean("done",true).apply();expanded=false}) {Text("Concluir guia / ver depois")}
                Text("Guia opcional. Reabra quando quiser. As demais áreas estão no menu.",style=MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable fun RhythmInsight(rows:List<TrainingRecord>,available:Boolean) {
    val days=workoutRhythm(rows,today())
    var table by rememberSaveable {mutableStateOf(false)}
    Panel("Seu ritmo · últimos 7 dias") {
        if(!available) Text("Aguardando seu histórico. Nenhum valor foi tratado como zero.") else {
            Text("${days.count {it.sessions>0}} dias com treino · ${days.sumOf {it.sessions}} sessões")
            val highest=(days.maxOfOrNull {it.sessions} ?: 1).coerceAtLeast(1)
            Row(Modifier.fillMaxWidth().height(132.dp),horizontalArrangement=Arrangement.spacedBy(6.dp),verticalAlignment=Alignment.Bottom) {
                days.forEach {day ->
                    Column(Modifier.weight(1f).semantics {contentDescription="${day.date}: ${day.sessions} sessões"},horizontalAlignment=Alignment.CenterHorizontally) {
                        Text("${day.sessions}",style=MaterialTheme.typography.labelSmall)
                        Spacer(Modifier.height(5.dp))
                        Box(Modifier.width(18.dp).height((4+day.sessions.toFloat()/highest*78).dp).background(MaterialTheme.colorScheme.primary,MaterialTheme.shapes.small))
                        Text(day.date.format(DateTimeFormatter.ofPattern("dd/MM")),style=MaterialTheme.typography.labelSmall)
                    }
                }
            }
            TextButton({table=!table}) {Text(if(table) "Recolher valores" else "Ler valores do gráfico")}
            if(table) days.forEach {Text("${it.date.format(DateTimeFormatter.ofPattern("dd/MM"))}: ${it.sessions} sessões · ${it.reps} rep · ${formatOneDecimal(it.km)} km",style=MaterialTheme.typography.bodyMedium)}
            Text(if(days.none {it.sessions>0}) "Seu gráfico começa com o primeiro treino salvo." else "Seu ritmo pode variar. Descanso não remove XP.",style=MaterialTheme.typography.bodySmall)
        }
    }
}

private data class WorkoutMedia(val title:String,val uri:String,val type:String)

@Composable fun WorkoutMediaPanel() {
    val context=LocalContext.current
    val owner=LocalGpsAccount.current
    val prefs=remember(owner) {context.getSharedPreferences("solem_media_$owner",Context.MODE_PRIVATE)}
    var items by remember(owner) {mutableStateOf(runCatching {
        val data=JSONArray(prefs.getString("items","[]"))
        (0 until data.length()).map {val o=data.getJSONObject(it);WorkoutMedia(o.getString("title"),o.getString("uri"),o.getString("type"))}
            .filter {it.uri.startsWith("content://") || validMotivationLink(it.uri)}.take(8)
    }.getOrDefault(emptyList()))}
    var expanded by rememberSaveable {mutableStateOf(false)}
    var selected by remember {mutableStateOf<WorkoutMedia?>(null)}
    var title by rememberSaveable {mutableStateOf("")}
    var url by rememberSaveable {mutableStateOf("")}
    var error by remember {mutableStateOf<String?>(null)}
    fun save(new:List<WorkoutMedia>) {
        val data=JSONArray();new.forEach {data.put(JSONObject().put("title",it.title).put("uri",it.uri).put("type",it.type))}
        if(prefs.edit().putString("items",data.toString()).commit()) {items=new;error=null}
        else error="Não foi possível guardar o favorito neste aparelho."
    }
    val picker=rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) {uri ->
        if(uri!=null) runCatching {
            context.contentResolver.takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION)
            val mime=context.contentResolver.getType(uri).orEmpty()
            require(mime.startsWith("audio/") || mime.startsWith("video/"))
            var name="Minha mídia"
            context.contentResolver.query(uri,arrayOf(android.provider.OpenableColumns.DISPLAY_NAME),null,null,null)?.use {if(it.moveToFirst()) name=it.getString(0)}
            if(items.none {it.uri==uri.toString()} && items.size<8) save(items+WorkoutMedia(name.take(80),uri.toString(),if(mime.startsWith("audio/")) "audio" else "video"))
        }.onFailure {error="Não foi possível abrir este arquivo. Escolha um áudio ou vídeo disponível no aparelho."}
    }
    OutlinedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
            TextButton({expanded=!expanded; if(!expanded) selected=null},modifier=Modifier.fillMaxWidth()) {Text(if(expanded) "Recolher minha trilha de treino" else "Minha trilha de treino · músicas e clipes")}
            if(expanded) {
                Text("Sua música, seu ritmo.",style=MaterialTheme.typography.titleLarge)
                Text("Arquivos e favoritos ficam nesta conta, neste aparelho. Nada toca automaticamente. Ao sair da tela ou bloquear o celular, a mídia local pausa; para ouvir em segundo plano, use seu serviço de música.",style=MaterialTheme.typography.bodySmall)
                items.forEach {item ->
                    Row(verticalAlignment=Alignment.CenterVertically) {
                        TextButton({
                            if(item.type=="link") runCatching {context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(item.uri)))}.onFailure {error="Nenhum aplicativo disponível para abrir este link."}
                            else selected=item
                        },modifier=Modifier.weight(1f)) {Text(item.title)}
                        TextButton({if(selected==item) selected=null;save(items-item)}) {Text("Remover")}
                    }
                }
                selected?.let {item -> key(item.uri) {LocalWorkoutPlayer(item.uri,item.type)}}
                OutlinedButton({picker.launch(arrayOf("audio/*","video/*"))},enabled=items.size<8,modifier=Modifier.fillMaxWidth()) {Text("Escolher áudio ou vídeo")}
                Field("Nome da playlist ou clipe",title) {title=it.take(80)}
                Field("Link do YouTube, Spotify ou SoundCloud",url) {url=it.take(500)}
                Button({
                    if(title.isBlank() || !validMotivationLink(url.trim())) error="Informe um nome e um link HTTPS do YouTube, Spotify ou SoundCloud."
                    else if(items.any {it.uri==url.trim()}) error="Este favorito já está salvo."
                    else {save(items+WorkoutMedia(title.trim(),url.trim(),"link"));title="";url=""}
                },enabled=items.size<8) {Text("Guardar link")}
                error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
                Text("Até 8 favoritos. Clipes externos podem ter flashes. Prefira áudio se isso causar desconforto.",style=MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable private fun LocalWorkoutPlayer(uri:String,type:String) {
    val context=LocalContext.current
    val lifecycle=LocalLifecycleOwner.current.lifecycle
    var player by remember {mutableStateOf<MediaPlayer?>(null)}
    var video by remember {mutableStateOf<VideoView?>(null)}
    var loading by remember {mutableStateOf(false)}
    var playing by remember {mutableStateOf(false)}
    var error by remember {mutableStateOf(false)}
    DisposableEffect(uri,lifecycle) {
        val observer=LifecycleEventObserver {_,event -> if(event==Lifecycle.Event.ON_STOP) {
            runCatching {player?.pause();video?.pause()};playing=false
        }}
        lifecycle.addObserver(observer)
        onDispose {lifecycle.removeObserver(observer);player?.release();video?.stopPlayback()}
    }
    if(type=="video") AndroidView(factory={VideoView(it).also {view ->
        video=view;view.setVideoURI(Uri.parse(uri))
        view.setMediaController(MediaController(it).also {controls -> controls.setAnchorView(view)})
        view.setOnCompletionListener {playing=false}
        view.setOnErrorListener {_,_,_ -> error=true;loading=false;playing=false;true}
    }},modifier=Modifier.fillMaxWidth().height(210.dp))
    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        Button({
            error=false
            if(type=="video") {video?.start();playing=true}
            else if(player!=null) {runCatching {player?.start();playing=true}.onFailure {error=true;player?.release();player=null}}
            else {
                loading=true
                runCatching {
                    val created=MediaPlayer()
                    player=created
                    created.apply {
                        setDataSource(context,Uri.parse(uri))
                        setOnPreparedListener {loading=false;if(lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) {it.start();playing=true}}
                        setOnCompletionListener {playing=false}
                        setOnErrorListener {failed,_,_ -> error=true;loading=false;playing=false;failed.release();player=null;true}
                        prepareAsync()
                    }
                }.onFailure {loading=false;error=true;player?.release();player=null}
            }
        },enabled=!loading && !playing) {Text(if(loading) "Preparando…" else "Reproduzir")}
        OutlinedButton({runCatching {player?.pause();video?.pause()};playing=false},enabled=!loading) {Text("Pausar")}
    }
    if(error) Text("Não foi possível reproduzir. O arquivo pode ter sido movido ou ter um formato incompatível.",color=MaterialTheme.colorScheme.error)
}
