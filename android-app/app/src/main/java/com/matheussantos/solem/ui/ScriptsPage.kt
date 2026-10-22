package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.gestures.scrollBy
import androidx.compose.foundation.interaction.collectIsDraggedAsState
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import java.util.UUID

@Composable fun ScriptsPage(vm:WorkspaceViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    var search by rememberSaveable {mutableStateOf("")}
    var trash by rememberSaveable {mutableStateOf(false)}
    var selected by rememberSaveable {mutableStateOf<String?>(null)}
    var reading by remember {mutableStateOf<PersonalItem?>(null)}
    LaunchedEffect(Unit) {vm.refresh()}
    val documents=state.items.filter {scriptDocument(it)!=null && it.archived==trash && (it.title+it.body).contains(search,true)}
    val old=state.items.firstOrNull {it.id==selected && !it.archived}
    Page("Ideias e roteiros") {
        Text("Seu espaço privado para criar e ensaiar. O teleprompter não grava áudio ou vídeo.")
        if(state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        state.message?.let {Text(it,color=if(state.failed) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant)}
        TextButton({vm.refresh()},enabled=!state.busy) {Text("Atualizar documentos")}
        Field("Buscar título, texto ou tags",search) {search=it}
        Row {Checkbox(trash,{trash=it;selected=null});Text("Lixeira")}
        TextButton({selected=null}) {Text("＋ Nova ideia ou roteiro")}
        documents.forEach {item -> Panel(item.title) {
            val doc=scriptDocument(item)!!
            Text(if(doc.type=="script") "Roteiro" else "Ideia")
            if(doc.tags.isNotBlank()) Text(doc.tags)
            if(trash) TextButton({vm.archive(item)},enabled=!state.busy) {Text("Restaurar")}
            else {
                Row {TextButton({selected=item.id}) {Text("Editar")}
                    TextButton({reading=item},enabled=doc.text.isNotBlank()) {Text("▶ Teleprompter")}}
                TextButton({vm.archive(item);if(selected==item.id)selected=null},enabled=!state.busy) {Text("Mover para lixeira")}
            }
        } }
        if(!trash) key(selected,old?.revision) {
            val data=old?.let(::scriptDocument) ?: ScriptDocument()
            var title by rememberSaveable {mutableStateOf(old?.title.orEmpty())}
            var kind by rememberSaveable {mutableStateOf(if(data.type=="script") "Roteiro" else "Ideia")}
            var text by rememberSaveable {mutableStateOf(data.text)}
            var description by rememberSaveable {mutableStateOf(data.description)}
            var tags by rememberSaveable {mutableStateOf(data.tags)}
            var error by remember {mutableStateOf<String?>(null)}
            Text(if(old==null) "Novo documento" else "Editando: ${old.title}",style=MaterialTheme.typography.titleLarge)
            Choice("Tipo",kind,listOf("Ideia","Roteiro")) {kind=it}
            Field("Título",title) {title=it.take(160)}
            OutlinedTextField(description,{description=it.take(3000)},label={Text("Possível descrição")},modifier=Modifier.fillMaxWidth(),minLines=2)
            Field("Tags separadas por vírgula",tags) {tags=it.take(500)}
            OutlinedTextField(text,{text=it.take(40000)},label={Text("Ideia / texto do roteiro")},modifier=Modifier.fillMaxWidth(),minLines=8,maxLines=16)
            error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
            Button({try {
                val item=PersonalItem(old?.id ?: UUID.randomUUID().toString(),"note",title.trim(),scriptBody(ScriptDocument(if(kind=="Roteiro") "script" else "idea",text,description,tags)))
                validatePersonalItem(item);error=null;vm.save(item,old) {selected=it.id}
            } catch(e:Exception) {error=e.message}},enabled=!state.busy) {Text("Salvar documento")}
            Text("Salve antes de abrir a versão atualizada no teleprompter.",style=MaterialTheme.typography.bodySmall)
        }
    }
    reading?.let {item -> ScriptPrompter(item.title,scriptDocument(item)!!.text) {reading=null}}
}

@Composable private fun ScriptPrompter(title:String,text:String,close:()->Unit) {
    Dialog(onDismissRequest=close,properties=DialogProperties(usePlatformDefaultWidth=false)) {
        val scroll=rememberScrollState()
        var playing by remember {mutableStateOf(false)}
        var speed by rememberSaveable {mutableFloatStateOf(35f)}
        var size by rememberSaveable {mutableFloatStateOf(30f)}
        var status by remember {mutableStateOf("Pronto para ler")}
        val dragging by scroll.interactionSource.collectIsDraggedAsState()
        LaunchedEffect(dragging) {if(dragging) {playing=false;status="Pausado para rolagem manual"}}
        val view=LocalView.current
        val owner=LocalLifecycleOwner.current
        DisposableEffect(owner) {
            val observer=LifecycleEventObserver {_,event -> if(event==Lifecycle.Event.ON_PAUSE) {playing=false;status="Pausado ao sair da tela"}}
            owner.lifecycle.addObserver(observer)
            onDispose {owner.lifecycle.removeObserver(observer)}
        }
        DisposableEffect(playing,view) {val before=view.keepScreenOn;view.keepScreenOn=playing;onDispose {view.keepScreenOn=before}}
        LaunchedEffect(playing) {
            if(playing) {
                if(scroll.value>=scroll.maxValue) scroll.scrollTo(0)
                var last=withFrameNanos {it}
                while(playing) {
                    val now=withFrameNanos {it}
                    scroll.scrollBy(((now-last)/1e9).toFloat().coerceAtMost(.1f)*speed);last=now
                    if(scroll.value>=scroll.maxValue) {playing=false;status="Fim do roteiro"}
                }
            }
        }
        var reset by remember {mutableIntStateOf(0)}
        LaunchedEffect(reset) {scroll.scrollTo(0)}
        Surface(Modifier.fillMaxSize(),color=MaterialTheme.colorScheme.background) {
            Column(Modifier.fillMaxSize().padding(20.dp)) {
                Text(title,maxLines=2,style=MaterialTheme.typography.titleMedium)
                Row {Button({playing=!playing;status=if(playing) "Lendo" else "Pausado"}) {Text(if(playing) "Pausar" else "▶ Iniciar")}
                    TextButton({playing=false;reset++;status="Reiniciado"}) {Text("Reiniciar")}
                    TextButton(close) {Text("Fechar")}}
                Text("Velocidade: ${speed.toInt()} px/s")
                Slider(speed,{speed=it},valueRange=10f..120f)
                Text("Fonte: ${size.toInt()} · $status")
                Slider(size,{size=it;playing=false},valueRange=20f..60f)
                HorizontalDivider(color=MaterialTheme.colorScheme.primary)
                Box(Modifier.weight(1f).verticalScroll(scroll)) {
                    Text(text,Modifier.padding(top=24.dp,bottom=240.dp),fontSize=size.sp,lineHeight=(size*1.6f).sp)
                }
            }
        }
    }
}
