package com.matheussantos.solem.ui

import android.annotation.SuppressLint
import android.content.Intent
import android.net.Uri
import android.webkit.*
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*
import java.util.UUID

private class NoteDraft(val base: PersonalItem?, var folder: String, var event: NoteEditorEvent) {
    val reset = UUID.randomUUID().toString()
    var saved by mutableStateOf(false)
    var error by mutableStateOf("")
}

@Composable internal fun NotesLibrary(vm: WorkspaceViewModel, items: List<PersonalItem>, busy: Boolean, error: String?) {
    var folderId by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf<String?>(null) }
    var search by remember { mutableStateOf("") }
    var trash by remember { mutableStateOf(false) }
    var folderDialog by remember { mutableStateOf(false) }
    var rename by remember { mutableStateOf<PersonalItem?>(null) }
    val drafts = remember { mutableStateMapOf<String,NoteDraft>() }
    val folders = items.filter(::noteFolder)
    val notes = items.filter { it.kind == "note" && !noteFolder(it) && noteAttachment(it) == null &&
        scriptDocument(it) == null && vocabularyDocument(it) == null }
    if (folderDialog) {
        key(rename?.id) {
            var name by remember { mutableStateOf(rename?.title.orEmpty()) }
            val id = remember { rename?.id ?: UUID.randomUUID().toString() }
            AlertDialog(onDismissRequest={folderDialog=false}, title={Text(if(rename==null) "Nova pasta" else "Renomear pasta")},
                text={Field("Nome da pasta",name){name=it.take(160)}},
                confirmButton={TextButton({
                    val old=rename
                    vm.save(PersonalItem(id,"note",name.trim(),NOTE_FOLDER_PREFIX+"{}"),old) {
                        folderDialog=false
                        if(old==null) {folderId=id;selected=null}
                    }
                },enabled=!busy && name.isNotBlank()){Text(if(rename==null) "Criar pasta" else "Renomear")}},
                dismissButton={TextButton({folderDialog=false}){Text("Cancelar")}})
        }
    }
    if (selected == null) {
        Field("Buscar anotações",search){search=it}
        Row {
            TextButton({folderId=""}) {Text("Todas")}
            TextButton({rename=null;folderDialog=true},enabled=!busy) {Text("Nova pasta")}
            TextButton({trash=!trash;folderId=""}) {Text(if(trash) "Voltar à biblioteca" else "Lixeira")}
        }
        folders.filter {it.archived==trash}.forEach { folder ->
            Row(Modifier.fillMaxWidth()) {
                TextButton({folderId=folder.id},Modifier.weight(1f)) {Text("▱ "+folder.title)}
                var menu by remember(folder.id) {mutableStateOf(false)}
                Box {
                    TextButton({menu=true}) {Text("⋯")}
                    DropdownMenu(menu,{menu=false}) {
                        DropdownMenuItem(text={Text("Renomear")},onClick={menu=false;rename=folder;folderDialog=true})
                        DropdownMenuItem(text={Text(if(trash) "Restaurar pasta" else "Mover pasta para a lixeira")},
                            onClick={menu=false;vm.archive(folder);folderId=""},enabled=!busy)
                    }
                }
            }
        }
        HorizontalDivider()
        Text(folders.find {it.id==folderId}?.title ?: "Suas anotações",style=MaterialTheme.typography.titleLarge)
        if(!trash) Button({
            val id=UUID.randomUUID().toString()
            drafts[id]=NoteDraft(null,folderId,NoteEditorEvent("draft","", "",listOf(NoteBlock(UUID.randomUUID().toString(),"text")),emptyMap()))
            selected=id
        }) {Text("Nova anotação")}
        val visible = notes.filter { note ->
            val doc=noteDocument(note,items)
            val parent=folders.find {it.id==doc.folder}
            (note.archived || parent?.archived==true)==trash && (folderId.isEmpty() || doc.folder==folderId) &&
                (note.title+" "+doc.blocks.joinToString(" "){it.text}).contains(search,true)
        }
        if(visible.isEmpty()) Text("Nenhuma anotação aqui.",style=MaterialTheme.typography.bodyMedium)
        visible.forEach { note ->
            Row(Modifier.fillMaxWidth()) {
                TextButton({
                    if(!trash) {
                        val doc=noteDocument(note,items)
                        if(note.id !in drafts) drafts[note.id]=NoteDraft(note,doc.folder,
                            NoteEditorEvent("draft","",note.title,doc.blocks,noteImages(note.id,items)))
                        selected=note.id
                    }
                },Modifier.weight(1f),enabled=!trash){Text(note.title)}
                if(trash && folders.none {it.id==noteDocument(note,items).folder && it.archived})
                    TextButton({vm.archive(note)},enabled=!busy){Text("Restaurar")}
            }
        }
    } else {
        val id=selected!!
        val draft=drafts.getValue(id)
        Row {
            TextButton({selected=null}) {Text("← Biblioteca")}
            var menu by remember(id) {mutableStateOf(false)}
            Box {
                TextButton({menu=true}) {Text("⋯")}
                DropdownMenu(menu,{menu=false}) {
                    val latest=notes.find {it.id==id}
                    if(latest!=null) {
                        DropdownMenuItem(text={Text("Mover para a lixeira")},onClick={menu=false;vm.archive(latest);selected=null},enabled=!busy)
                        DropdownMenuItem(text={Text("Recarregar versão salva")},onClick={
                            menu=false
                            val doc=noteDocument(latest,items)
                            drafts[id]=NoteDraft(latest,doc.folder,NoteEditorEvent("draft","",latest.title,doc.blocks,noteImages(id,items)))
                        })
                    }
                }
            }
        }
        val destinations=listOf("" to "Sem pasta")+folders.filterNot {it.archived}.map {it.id to it.title}
        var moveMenu by remember {mutableStateOf(false)}
        Box {
            OutlinedButton({moveMenu=true}) {Text("Pasta · "+(destinations.find {it.first==draft.folder}?.second ?: "Sem pasta"))}
            DropdownMenu(moveMenu,{moveMenu=false}) {
                destinations.forEach { (dest,label) ->
                    DropdownMenuItem(text={Text(label)},onClick={draft.folder=dest;moveMenu=false})
                }
            }
        }
        key(id,draft.reset) {
            InlineNoteEditor(draft,busy,error) { event ->
                draft.event=event
                draft.saved=false
                if(event.action=="save") {
                    try {
                        val (note,assets)=prepareNote(id,draft.folder,event,items)
                        draft.error=""
                        vm.saveNote(note,assets,draft.base) { saved ->
                            val updated=NoteDraft(saved,draft.folder,event)
                            updated.saved=true
                            drafts[id]=updated
                        }
                    } catch(e:IllegalArgumentException) { draft.error=e.message ?: "Confira o conteúdo.";drafts[id]=draft }
                }
            }
        }
    }
}

private class NoteBridge(val receive:(String)->Unit) {
    @JavascriptInterface fun postMessage(value:String) {receive(value)}
}

@SuppressLint("SetJavaScriptEnabled")
@Composable private fun InlineNoteEditor(draft:NoteDraft,busy:Boolean,error:String?,onEvent:(NoteEditorEvent)->Unit) {
    val context=LocalContext.current
    val receive by rememberUpdatedState(onEvent)
    var fileCallback by remember {mutableStateOf<ValueCallback<Array<Uri>>?>(null)}
    val picker=rememberLauncherForActivityResult(ActivityResultContracts.GetMultipleContents()) {uris ->
        fileCallback?.onReceiveValue(uris.takeIf {it.isNotEmpty()}?.toTypedArray())
        fileCallback=null
    }
    val html=remember {context.assets.open("note_editor/index.html").bufferedReader().use {it.readText()}}
    fun args()=buildJsonObject {
        put("title",draft.event.title)
        put("blocks",notesJson.encodeToJsonElement(draft.event.blocks))
        put("images",notesJson.encodeToJsonElement(draft.event.images))
        put("reset",draft.reset)
        put("saved",draft.saved)
        put("error",draft.error.ifBlank {error.orEmpty()})
        put("busy",busy)
    }.toString()
    AndroidView(modifier = Modifier.fillMaxWidth().height(660.dp),
        factory={ctx ->
            WebView(ctx).apply {
                setBackgroundColor(android.graphics.Color.rgb(12,20,32))
                settings.javaScriptEnabled=true
                settings.allowFileAccess=false
                settings.allowContentAccess=true
                settings.blockNetworkLoads=true
                addJavascriptInterface(NoteBridge { raw ->
                    post {runCatching {notesJson.decodeFromString<NoteEditorEvent>(raw)}.onSuccess {receive(it)}}
                },"SolemNotes")
                webViewClient=object:WebViewClient() {
                    override fun onPageFinished(view:WebView,url:String) {view.evaluateJavascript("window.loadNote("+args()+");",null)}
                    override fun shouldOverrideUrlLoading(view:WebView,request:WebResourceRequest):Boolean {
                        if(request.hasGesture() && request.url.scheme in listOf("http","https"))
                            runCatching {context.startActivity(Intent(Intent.ACTION_VIEW,request.url))}
                        return true
                    }
                }
                webChromeClient=object:WebChromeClient() {
                    override fun onShowFileChooser(view:WebView,callback:ValueCallback<Array<Uri>>,params:FileChooserParams):Boolean {
                        fileCallback?.onReceiveValue(null)
                        fileCallback=callback
                        picker.launch("image/*")
                        return true
                    }
                }
                loadDataWithBaseURL("https://solem.local/",html,"text/html","UTF-8",null)
            }
        },
        update={it.evaluateJavascript("if(window.loadNote)window.loadNote("+args()+");",null)},
        onRelease={fileCallback?.onReceiveValue(null);fileCallback=null;it.removeJavascriptInterface("SolemNotes");it.destroy()})
}
