package com.matheussantos.solem.ui

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Base64
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.ByteArrayOutputStream
import java.net.URI
import java.util.UUID

private const val prefix = "solem-note-material-v1\n"
@Serializable internal data class NoteMaterial(val folder: String, val type: String, val value: String)
internal fun noteMaterial(item: PersonalItem): NoteMaterial? {
    if (item.kind != "note" || !item.body.startsWith(prefix)) return null
    return runCatching {
        Json.decodeFromString<NoteMaterial>(item.body.removePrefix(prefix)).also {
            UUID.fromString(it.folder)
            require(it.type in listOf("image", "reference", "link"))
        }
    }.getOrNull()
}

private fun webLink(value: String) = runCatching {
    val uri = URI(value)
    uri.scheme?.lowercase() in setOf("http", "https") && !uri.host.isNullOrBlank()
}.getOrDefault(false)

private fun compactImage(context: Context, uri: Uri): String {
    val resolver = context.contentResolver
    val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, bounds) }
    require(bounds.outWidth > 0 && bounds.outHeight > 0 && bounds.outWidth.toLong() * bounds.outHeight <= 24000000)
    val options = BitmapFactory.Options()
    while (maxOf(bounds.outWidth, bounds.outHeight) / options.inSampleSize.coerceAtLeast(1) > 1200)
        options.inSampleSize = options.inSampleSize.coerceAtLeast(1) * 2
    var bitmap = resolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, options) }
        ?: error("Não foi possível abrir a imagem.")
    try {
        val output = ByteArrayOutputStream()
        while (true) {
            output.reset()
            check(bitmap.compress(Bitmap.CompressFormat.JPEG, 80, output))
            if (output.size() <= 35000) return Base64.encodeToString(output.toByteArray(), Base64.NO_WRAP)
            val smaller = Bitmap.createScaledBitmap(bitmap, (bitmap.width * 3 / 4).coerceAtLeast(1), (bitmap.height * 3 / 4).coerceAtLeast(1), true)
            bitmap.recycle()
            bitmap = smaller
        }
    } finally { bitmap.recycle() }
}

@Composable internal fun FolderMaterials(vm: WorkspaceViewModel, folder: PersonalItem,
    materials: List<Pair<PersonalItem,NoteMaterial>>, busy: Boolean) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val links = LocalUriHandler.current
    val types = mapOf("Imagem" to "image", "Link" to "link", "Referência" to "reference")
    var type by remember { mutableStateOf("Imagem") }
    var title by remember { mutableStateOf("") }
    var value by remember { mutableStateOf("") }
    var image by remember { mutableStateOf("") }
    var processing by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }
    var trash by remember { mutableStateOf(false) }
    var draftId by remember { mutableStateOf(UUID.randomUUID().toString()) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) scope.launch {
            processing = true
            image = ""
            try { image = withContext(Dispatchers.IO) { compactImage(context, uri) }; error = "" }
            catch (_: Exception) { error = "Escolha uma imagem válida de até 24 megapixels." }
            finally { processing = false }
        }
    }
    Row { Checkbox(trash,{trash=it}); Text("Lixeira desta pasta") }
    materials.filter { it.first.archived == trash }.forEach { (item, data) ->
        key(item.id) {
            var expanded by remember { mutableStateOf(false) }
            TextButton({expanded=!expanded}) { Text(item.title) }
            if (expanded) {
                if (!trash) when (data.type) {
                    "link" -> if (webLink(data.value)) OutlinedButton({runCatching { links.openUri(data.value) }.onFailure {error="Não foi possível abrir o link."}}) {Text("Abrir link")}
                    "reference" -> Text(data.value)
                    "image" -> {
                        val picture = remember(data.value) { runCatching {
                            val bytes = Base64.decode(data.value, Base64.DEFAULT)
                            BitmapFactory.decodeByteArray(bytes,0,bytes.size)?.asImageBitmap()
                        }.getOrNull() }
                        if (picture != null) Image(picture, item.title, Modifier.fillMaxWidth().heightIn(max=420.dp))
                    }
                }
                TextButton({vm.archive(item)},enabled=!busy) {Text(if(trash) "Restaurar material" else "Mover material para a lixeira")}
            }
        }
    }
    if (trash) return
    Choice("Adicionar à pasta",type,types.keys.toList()) { type=it;value="";error="" }
    Field("Título do material",title) { title=it.take(160) }
    if(type=="Imagem") OutlinedButton({picker.launch("image/*")},enabled=!processing) {
        Text(if(processing) "Preparando imagem…" else if(image.isEmpty()) "Selecionar imagem · cópia compacta" else "Imagem selecionada · trocar")
    } else if(type=="Link") Field("Endereço http/https",value) {value=it.take(2000)}
    else OutlinedTextField(value,{value=it.take(16000)},label={Text("Referência ou trecho")})
    if(error.isNotEmpty()) Text(error,color=MaterialTheme.colorScheme.error)
    Button({
        val content = if(type=="Imagem") image else value.trim()
        if(type=="Link" && !webLink(content)) error="Informe um link http/https válido."
        else {
            val data=NoteMaterial(folder.id,types.getValue(type),content)
            val item=PersonalItem(draftId,"note",title.trim(),prefix+Json.encodeToString(data))
            vm.save(item,null) { title="";value="";image="";error="";draftId=UUID.randomUUID().toString() }
        }
    },enabled=!busy && !processing && title.isNotBlank() && (if(type=="Imagem") image.isNotEmpty() else value.isNotBlank())) {Text("Adicionar material")}
}
