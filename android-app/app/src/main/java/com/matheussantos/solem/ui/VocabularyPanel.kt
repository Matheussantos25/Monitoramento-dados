package com.matheussantos.solem.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.graphics.BitmapFactory
import android.text.Html
import android.widget.TextView
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.coroutines.CancellationException
import java.util.UUID

@Composable fun VocabularyPanel(vm:WorkspaceViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    var selected by rememberSaveable {mutableStateOf<String?>(null)}
    var trash by rememberSaveable {mutableStateOf(false)}
    var search by rememberSaveable {mutableStateOf("")}
    LaunchedEffect(Unit){vm.refresh()}
    Text("Seu baralho de vocabulário",style=MaterialTheme.typography.headlineSmall)
    Text("Frase na frente, significado e imagem no verso. Revise aqui ou exporte para o Anki.")
    state.message?.let {Text(it,color=if(state.failed)MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)}
    if(state.busy)LinearProgressIndicator(Modifier.fillMaxWidth())
    var mode by rememberSaveable {mutableStateOf("Revisar")}
    Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
        listOf("Revisar","Criar e editar").forEach {name -> FilterChip(mode==name,{mode=name},label={Text(name)})}
    }
    if(mode=="Revisar") {VocabularyReviewPanel(state.items,state.busy,vm);return}
    Field("Buscar no caderno",search){search=it}
    Row {Checkbox(trash,{trash=it;selected=null});Text("Lixeira do vocabulário")}
    val items=state.items.filter {vocabularyDocument(it)!=null && it.archived==trash && (it.title+it.body).contains(search,true)}
    val options=listOf("＋ Nova palavra")+items.map {it.title+" · "+it.id.take(8)}
    val old=items.firstOrNull {it.id==selected}
    Choice("Palavra do caderno",old?.let {it.title+" · "+it.id.take(8)} ?: options[0],options) {choice -> selected=items.firstOrNull {it.title+" · "+it.id.take(8)==choice}?.id}
    if(trash) {
        old?.let {TextButton({vm.archive(it)},enabled=!state.busy){Text("Restaurar palavra")}}
    } else key(selected,old?.revision) {
        VocabularyEditor(old,state.busy,vm){selected=it}
        old?.let {TextButton({vm.archive(it);selected=null},enabled=!state.busy){Text("Mover palavra para a lixeira")}}
    }
}

@Composable private fun VocabularyEditor(old:PersonalItem?,busy:Boolean,vm:WorkspaceViewModel,onSaved:(String)->Unit) {
    val data=old?.let(::vocabularyDocument) ?: Vocabulary()
    var word by rememberSaveable {mutableStateOf(data.word)}
    var sentence by rememberSaveable {mutableStateOf(data.sentence)}
    var definition by rememberSaveable {mutableStateOf(data.definition)}
    var context by rememberSaveable {mutableStateOf(data.context)}
    var source by rememberSaveable {mutableStateOf(data.source)}
    var forms by rememberSaveable {mutableStateOf(data.forms)}
    var image by rememberSaveable {mutableStateOf(data.image)}
    var imagePage by rememberSaveable {mutableStateOf(data.image_page)}
    var credit by rememberSaveable {mutableStateOf(data.image_credit)}
    var imageTerm by rememberSaveable {mutableStateOf(data.word)}
    val newId=rememberSaveable {UUID.randomUUID().toString()}
    var senses by remember {mutableStateOf(emptyList<WordSense>())}
    var senseIndex by remember {mutableIntStateOf(0)}
    var imageChoices by remember {mutableStateOf(emptyList<WordImage>())}
    var pictureIndex by remember {mutableIntStateOf(0)}
    var loading by remember {mutableStateOf(false)}
    var message by remember {mutableStateOf("")}
    val scope=rememberCoroutineScope()
    val androidContext=LocalContext.current
    var packageBytes by remember {mutableStateOf<ByteArray?>(null)}
    val export=rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/zip")) {uri ->
        if(uri!=null) {
            val bytes=packageBytes
            if(bytes==null)message="A tela foi recriada. Prepare o pacote novamente."
            else scope.launch {
                try {withContext(Dispatchers.IO){androidContext.contentResolver.openOutputStream(uri)?.use {it.write(bytes)} ?: error("output")};message="Pacote salvo. Leia as instruções dentro do ZIP."}
                catch(e:CancellationException){throw e}
                catch(e:Exception){message="Não foi possível salvar o pacote. Tente novamente."}
                finally {packageBytes=null}
            }
        } else packageBytes=null
    }
    Field("Palavra ou expressão em inglês",word){word=it.take(100);senses=emptyList();forms=""}
    Text("Buscar envia apenas a palavra ao FreeDictionaryAPI.com. Imagens usam o termo informado no Wikimedia Commons. Sem API paga.",style=MaterialTheme.typography.bodySmall)
    OutlinedButton({val query=word;loading=true;message="";scope.launch {
        try {val result=withContext(Dispatchers.IO){VocabularyLookup.dictionary(query)};if(word==query){senses=result;senseIndex=0};if(result.isEmpty())message="Sem resultado. Você pode preencher manualmente e salvar a palavra."}
        catch(e:CancellationException){throw e}
        catch(e:Exception){message="Dicionário indisponível ou palavra não encontrada. Seus campos continuam aqui."}
        finally {loading=false}
    }},enabled=!loading && word.isNotBlank()){Text("Buscar significado e exemplo")}
    if(senses.isNotEmpty()) {
        val labels=senses.mapIndexed {i,s->"${i+1}. ${s.part} · ${s.definition}"}
        Choice("Sentido usado na cena",labels[senseIndex],labels){senseIndex=labels.indexOf(it)}
        val sense=senses[senseIndex]
        if(sense.sentence.isNotBlank())Text("Exemplo: "+sense.sentence) else Text("Sem exemplo neste sentido. Use a frase da série.")
        TextButton({definition=sense.definition;source=sense.source;forms=sense.forms}){Text("Usar este significado")}
        if(sense.sentence.isNotBlank())TextButton({sentence=sense.sentence;source=sense.source;forms=sense.forms}){Text("Usar exemplo do dicionário")}
    }
    Text("Front · Frente",style=MaterialTheme.typography.titleMedium)
    Text("A palavra informada acima aparece em negrito no cartão.",style=MaterialTheme.typography.bodySmall)
    OutlinedTextField(sentence,{sentence=it.take(2000)},label={Text("Frase em inglês")},modifier=Modifier.fillMaxWidth(),minLines=2)
    Text("Back · Verso",style=MaterialTheme.typography.titleMedium)
    OutlinedTextField(definition,{definition=it.take(3000)},label={Text("Significado em inglês")},modifier=Modifier.fillMaxWidth(),minLines=2)
    Field("Série, episódio ou contexto (opcional)",context){context=it.take(300)}
    if(source.isNotBlank())Text(source,style=MaterialTheme.typography.bodySmall)
    var showImages by rememberSaveable {mutableStateOf(false)}
    TextButton({showImages=!showImages;if(imageTerm.isBlank())imageTerm=word}){Text(if(showImages)"Fechar busca de imagem" else "Adicionar / trocar imagem")}
    if(showImages) {
        Field("O que a imagem deve mostrar?",imageTerm){imageTerm=it.take(100)}
        OutlinedButton({val term=imageTerm;loading=true;scope.launch {
            try {imageChoices=withContext(Dispatchers.IO){VocabularyLookup.images(term)};pictureIndex=0;if(imageChoices.isEmpty())message="Sem imagens. Tente um termo mais concreto."}
            catch(e:CancellationException){throw e}
            catch(e:Exception){message="Busca indisponível. Você pode continuar sem imagem."}
            finally {loading=false}
        }},enabled=!loading && imageTerm.isNotBlank()){Text("Buscar imagens gratuitas")}
        if(imageChoices.isNotEmpty()) {
            val labels=imageChoices.map {it.title}
            Choice("Imagem sugerida",labels[pictureIndex],labels){pictureIndex=labels.indexOf(it)}
            val picture=imageChoices[pictureIndex]
            VocabularyImage(picture.image,word)
            Text(picture.image_credit,style=MaterialTheme.typography.bodySmall)
            TextButton({image=picture.image;imagePage=picture.image_page;credit=picture.image_credit;showImages=false}){Text("Usar esta imagem")}
        }
    }
    if(image.isNotBlank())TextButton({image="";imagePage="";credit=""}){Text("Remover imagem selecionada")}
    if(loading)LinearProgressIndicator(Modifier.fillMaxWidth())
    if(message.isNotBlank())Text(message)
    val current=Vocabulary(word.trim(),sentence,definition,context,source,image,imagePage,credit,forms,review=data.review)
    Button({try {
        val item=PersonalItem(old?.id ?: newId,"note",word.trim(),vocabularyBody(current))
        vm.save(item,old){onSaved(it.id)}
    } catch(e:Exception){message=e.message.orEmpty()}},enabled=!busy && !loading && word.isNotBlank(),modifier=Modifier.fillMaxWidth()){Text(if(old==null)"Salvar palavra" else "Salvar alterações da palavra")}
    val card=runCatching {vocabularyCard(current)}
    if(card.isFailure)Text(card.exceptionOrNull()?.message.orEmpty(),style=MaterialTheme.typography.bodySmall)
    else {
        val (front,back)=card.getOrThrow()
        Panel("Prévia · frente") {VocabularyHtml(front)}
        Panel("Prévia · verso") {
            VocabularyHtml(vocabularyCard(current.copy(image="")).second)
            if(image.isNotBlank()){VocabularyImage(image,word);Text(credit,style=MaterialTheme.typography.bodySmall)}
        }
        fun copy(label:String,html:String){
            val manager=androidContext.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            manager.setPrimaryClip(ClipData.newHtmlText(label,Html.fromHtml(html,Html.FROM_HTML_MODE_LEGACY).toString(),html))
            message="Copiado. Cole no Anki e confira a formatação."
        }
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            OutlinedButton({copy("Frente",front)},Modifier.weight(1f)){Text("Copiar frente")}
            OutlinedButton({copy("Verso",back)},Modifier.weight(1f)){Text("Copiar verso")}
        }
        Text("Imagens coladas por link precisam de internet. Para levar a imagem offline, exporte o pacote e importe no Anki para computador; depois sincronize.",style=MaterialTheme.typography.bodySmall)
        OutlinedButton({loading=true;scope.launch {
            try {packageBytes=withContext(Dispatchers.IO){VocabularyLookup.pack(current)};export.launch("solem-anki.zip")}
            catch(e:CancellationException){throw e}
            catch(e:Exception){message="Não foi possível preparar a imagem. Remova-a ou escolha outra e tente novamente."}
            finally {loading=false}
        }},enabled=!loading){Text("Exportar pacote com imagem")}
        Text("ZIP com card.txt e imagem (não é .apkg). Copie a imagem para collection.media e importe o texto com HTML habilitado. Exportar não aumenta seu contador de cards adicionados.",style=MaterialTheme.typography.bodySmall)
    }
}

@Composable internal fun VocabularyHtml(html:String) {
    val color=MaterialTheme.colorScheme.onSurface.toArgb()
    AndroidView(factory={TextView(it).apply {textSize=18f;setTextIsSelectable(true)}},update={it.setTextColor(color);it.text=Html.fromHtml(html,Html.FROM_HTML_MODE_LEGACY)},modifier=Modifier.fillMaxWidth())
}
@Composable internal fun VocabularyImage(url:String,description:String) {
    val bitmap by produceState<android.graphics.Bitmap?>(null,url) {
        value=withContext(Dispatchers.IO) {runCatching {
            val bytes=VocabularyLookup.imageBytes(url).first
            val bounds=BitmapFactory.Options().apply {inJustDecodeBounds=true};BitmapFactory.decodeByteArray(bytes,0,bytes.size,bounds)
            val options=BitmapFactory.Options();while(bounds.outWidth/options.inSampleSize.coerceAtLeast(1)>800 || bounds.outHeight/options.inSampleSize.coerceAtLeast(1)>800)options.inSampleSize=options.inSampleSize.coerceAtLeast(1)*2
            BitmapFactory.decodeByteArray(bytes,0,bytes.size,options)
        }.getOrNull()}
    }
    bitmap?.let {Image(it.asImageBitmap(),description,modifier=Modifier.fillMaxWidth().heightIn(max=260.dp))}
        ?: Text("Imagem carregando ou indisponível. Você pode continuar sem ela.",style=MaterialTheme.typography.bodySmall)
}
