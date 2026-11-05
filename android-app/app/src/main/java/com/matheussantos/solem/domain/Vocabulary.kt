package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.PersonalItem
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.*
import java.net.URI
import java.net.URLEncoder
import java.net.HttpURLConnection
import java.io.ByteArrayOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream
import java.security.MessageDigest

const val VOCAB_PREFIX="SOLEM_VOCAB_V1\n"
@Serializable data class Vocabulary(val word:String="",val sentence:String="",val definition:String="",val context:String="",val source:String="",val image:String="",val image_page:String="",val image_credit:String="",val forms:String="",val review:VocabularyReview?=null)
data class WordSense(val definition:String,val sentence:String,val part:String,val source:String,val forms:String="")
data class WordImage(val image:String,val image_page:String,val image_credit:String,val title:String)
private val vocabJson=Json {ignoreUnknownKeys=true}
fun vocabularyDocument(item:PersonalItem):Vocabulary? = if(item.kind!="note" || !item.body.startsWith(VOCAB_PREFIX)) null else runCatching {vocabJson.decodeFromString<Vocabulary>(item.body.removePrefix(VOCAB_PREFIX))}.getOrNull()
fun vocabularyBody(v:Vocabulary):String {
    require(v.word.isNotBlank() && v.word.length<=100 && v.sentence.length<=2000 && v.definition.length<=3000 && v.context.length<=300 && v.source.length<=1500 && v.forms.length<=2000 && v.image.length<=2000 && v.image_page.length<=2000 && v.image_credit.length<=2000) {"Informe uma palavra e reduza campos muito longos."}
    require(v.image.isBlank() || vocabularyMediaUrl(v.image)) {"Escolha uma imagem do Wikimedia Commons."}
    return VOCAB_PREFIX+vocabJson.encodeToString(v)
}
fun vocabularyMediaUrl(url:String):Boolean=runCatching {val u=URI(url);u.scheme=="https" && u.host in setOf("upload.wikimedia.org","thumb.wikimedia.org") && u.userInfo==null && u.port in setOf(-1,443)}.getOrDefault(false)
fun vocabEscape(s:String)=s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\"","&quot;").replace("'","&#x27;").replace("\n","<br>")
fun vocabularyFront(sentence:String,word:String,forms:String=""):String {
    if(word.isBlank())return vocabEscape(sentence)
    val pattern=Regex("(?<![\\p{L}\\p{N}_])"+"(?:"+(listOf(word.trim())+forms.lines().filter {it.isNotBlank()}).distinct().sortedByDescending {it.length}.joinToString("|"){Regex.escape(it)}+")"+"(?![\\p{L}\\p{N}_])",RegexOption.IGNORE_CASE)
    var end=0
    return buildString {pattern.findAll(sentence).forEach {append(vocabEscape(sentence.substring(end,it.range.first)));append("<b>"+vocabEscape(it.value)+"</b>");end=it.range.last+1};append(vocabEscape(sentence.substring(end)))}
}
fun vocabularyCard(v:Vocabulary,imageOverride:String?=null):Pair<String,String> {
    require(v.sentence.isNotBlank() && v.definition.isNotBlank()) {"Complete a frase e o significado em inglês antes de exportar."}
    val front=vocabularyFront(v.sentence,v.word,v.forms)
    require(front.contains("<b>")) {"A palavra precisa aparecer na frase. Use a forma que ouviu na série."}
    var back="<p>"+vocabEscape(v.definition)+"</p>"
    val image=imageOverride ?: v.image
    if(image.isNotBlank() && (imageOverride!=null || vocabularyMediaUrl(image))) back+="<p><img src=\""+vocabEscape(image)+"\" alt=\""+vocabEscape(v.word)+"\" style=\"max-width:100%;max-height:320px\"></p><small>"+vocabEscape(v.image_credit)+"<br>"+vocabEscape(v.image_page)+"</small>"
    if(v.source.isNotBlank()) back+="<p><small>"+vocabEscape(v.source)+"</small></p>"
    return front to back
}
fun vocabularyAnkiText(v:Vocabulary,imageOverride:String?=null):String {
    val (front,back)=vocabularyCard(v,imageOverride)
    fun field(s:String)="\""+s.replace("\"","\"\"")+"\""
    return "#separator:Tab\n#html:true\n#columns:Front\tBack\n"+field(front)+"\t"+field(back)+"\n"
}
private fun enc(s:String)=URLEncoder.encode(s,"UTF-8").replace("+","%20")
private fun JsonObject.text(k:String)=this[k]?.jsonPrimitive?.contentOrNull.orEmpty()
private fun JsonObject.array(k:String)=this[k] as? JsonArray ?: JsonArray(emptyList())
private fun plain(s:String)=s.replace(Regex("<[^>]*>")," ").replace("&amp;","&").replace("&quot;","\"").replace("&#39;","'").replace("&lt;","<").replace("&gt;",">").trim()
object VocabularyLookup {
    // Called on Dispatchers.IO only. Exact provider URLs; no redirects or arbitrary URL fetching.
    private fun fetch(url:String,limit:Int=1_500_000):Pair<ByteArray,String> {
        val c=URI(url).toURL().openConnection() as HttpURLConnection
        c.connectTimeout=12000;c.readTimeout=12000;c.instanceFollowRedirects=false
        c.setRequestProperty("User-Agent","Solem/0.21 (https://github.com/Matheussantos25/Monitoramento-dados)")
        try {
            require(c.responseCode==200) {"Serviço indisponível ou palavra não encontrada. Tente novamente ou preencha manualmente."}
            val bytes=c.inputStream.use {input -> val out=ByteArrayOutputStream();val buffer=ByteArray(8192);var n=input.read(buffer);while(n!=-1){require(out.size()+n<=limit){"Resposta muito grande. Escolha outra imagem."};out.write(buffer,0,n);n=input.read(buffer)};out.toByteArray()}
            return bytes to c.contentType.orEmpty().substringBefore(';')
        } finally {c.disconnect()}
    }
    fun dictionary(word:String):List<WordSense> {
        require(word.isNotBlank() && word.length<=100)
        val root=vocabJson.parseToJsonElement(String(fetch("https://freedictionaryapi.com/api/v1/entries/en/"+enc(word.trim())).first,Charsets.UTF_8)).jsonObject
        val source="FreeDictionaryAPI.com · Wiktionary · CC BY-SA 4.0 · https://en.wiktionary.org/wiki/"+enc(word.trim())
        return root.array("entries").flatMap {entry -> val e=entry.jsonObject
            if(e["language"]?.jsonObject?.text("code")!="en")emptyList() else e.array("senses").mapNotNull {sense -> val s=sense.jsonObject
                s.text("definition").takeIf {it.isNotBlank()}?.let {WordSense(it.take(3000),s.array("examples").firstOrNull()?.jsonPrimitive?.contentOrNull.orEmpty().take(2000),e.text("partOfSpeech"),source,e.array("forms").take(20).joinToString("\n"){it.jsonObject.text("word").take(100)})}
            }
        }.take(30)
    }
    fun images(term:String):List<WordImage> {
        val url="https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch="+enc(term.take(100)+" filetype:bitmap")+"&gsrnamespace=6&gsrlimit=6&prop=imageinfo&iiprop=url%7Cextmetadata%7Cmime&iiurlwidth=480"
        val root=vocabJson.parseToJsonElement(String(fetch(url).first,Charsets.UTF_8)).jsonObject
        return root["query"]?.jsonObject?.get("pages")?.jsonObject?.values.orEmpty().sortedBy {it.jsonObject["index"]?.jsonPrimitive?.intOrNull ?: 999}.mapNotNull {page ->
            val p=page.jsonObject;val i=p.array("imageinfo").firstOrNull()?.jsonObject ?: return@mapNotNull null
            val m=i["extmetadata"]?.jsonObject ?: return@mapNotNull null
            val license=plain(m["LicenseShortName"]?.jsonObject?.text("value").orEmpty())
            val image=i.text("thumburl")
            if(!vocabularyMediaUrl(image) || i.text("mime") !in listOf("image/jpeg","image/png") || license.isBlank())null
            else WordImage(image,i.text("descriptionurl"),(plain(m["Artist"]?.jsonObject?.text("value").orEmpty())+" · "+license+" · Wikimedia Commons").take(2000),p.text("title"))
        }
    }
    fun imageBytes(url:String):Pair<ByteArray,String> {
        require(vocabularyMediaUrl(url))
        return fetch(url,3_000_000).also {require(it.second in listOf("image/jpeg","image/png")){"Imagem indisponível. Escolha outra."}}
    }
    fun pack(v:Vocabulary):ByteArray {
        val media=if(v.image.isNotBlank())imageBytes(v.image) else null
        val filename=media?.let {"solem_"+MessageDigest.getInstance("SHA-256").digest(it.first).take(10).joinToString(""){b->"%02x".format(b)}+if(it.second=="image/png")".png" else ".jpg"}
        val out=ByteArrayOutputStream()
        ZipOutputStream(out).use {z -> fun entry(name:String,bytes:ByteArray){z.putNextEntry(ZipEntry(name));z.write(bytes);z.closeEntry()}
            entry("card.txt",vocabularyAnkiText(v,filename).toByteArray(Charsets.UTF_8))
            if(media!=null && filename!=null)entry("media/"+filename,media.first)
            entry("LEIA-ME.txt","No Anki para computador: extraia o ZIP. Copie o arquivo de media/ para collection.media do seu perfil. Importe card.txt como Básico (Front/Back), separado por tabulação, com HTML habilitado. Depois sincronize com o celular. Este ZIP não é um .apkg. Confira duplicatas na prévia. Fontes e créditos estão no verso. Exportar não registra cards adicionados nem tempo estudado no Solem.".toByteArray(Charsets.UTF_8))
        }
        return out.toByteArray()
    }
}
