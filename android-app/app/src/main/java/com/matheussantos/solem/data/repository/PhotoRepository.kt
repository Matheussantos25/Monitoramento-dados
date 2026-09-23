package com.matheussantos.solem.data.repository

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import com.matheussantos.solem.data.model.ProgressPhoto
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Order
import io.github.jan.supabase.storage.storage
import io.ktor.http.ContentType
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.util.UUID

class PhotoRepository(private val client: SupabaseClient) {
    private val bucket = client.storage.from("solem-progress-photos")

    suspend fun list(): List<ProgressPhoto> {
        check(client.auth.currentUserOrNull() != null) { "Entre novamente para abrir fotos privadas." }
        val rows = mutableListOf<ProgressPhoto>()
        while (true) {
            val page = client.from("solem_photos").select {
                order("day", Order.DESCENDING); order("id", Order.DESCENDING)
                range(rows.size.toLong(), rows.size.toLong() + 499)
            }.decodeList<ProgressPhoto>()
            rows.addAll(page)
            if (page.size < 500) return rows
        }
    }

    suspend fun upload(day: String, kind: String, bytes: ByteArray) {
        require(kind in listOf("face", "body"))
        val user = client.auth.currentUserOrNull() ?: error("Entre novamente para salvar a foto.")
        val jpeg = normalize(bytes)
        val id = UUID.randomUUID().toString()
        val path = "${user.id}/$id.jpg"
        val row = buildJsonObject { put("id", id); put("day", day); put("kind", kind); put("file_path", path) }
        val created = client.from("solem_photos").insert(row) { select() }.decodeList<ProgressPhoto>()
        require(created.size == 1) { "Não foi possível confirmar a foto." }
        try { bucket.upload(path, jpeg) { upsert = false; contentType = ContentType.Image.JPEG } }
        catch (error: Exception) {
            runCatching { client.from("solem_photos").delete { filter { eq("id", id) } } }
            throw error
        }
    }

    suspend fun download(photo: ProgressPhoto): ByteArray = bucket.downloadAuthenticated(photo.filePath).also {
        require(it.size <= 4 * 1024 * 1024 && it.size >= 3 && it[0] == 0xff.toByte() && it[1] == 0xd8.toByte()) { "Foto inválida." }
    }

    suspend fun delete(photo: ProgressPhoto) {
        bucket.delete(photo.filePath)
        client.from("solem_photos").delete { filter { eq("id", photo.id) } }
    }

    /** Re-encode as JPEG, removing EXIF including GPS location before upload. */
    internal fun normalize(raw: ByteArray): ByteArray {
        require(raw.isNotEmpty() && raw.size <= 8 * 1024 * 1024) { "Selecione imagem de até 8 MB." }
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(raw, 0, raw.size, bounds)
        require(bounds.outWidth > 0 && bounds.outHeight > 0 && bounds.outWidth.toLong() * bounds.outHeight <= 20_000_000) {
            "Imagem inválida ou acima de 20 megapixels."
        }
        var sample = 1
        while (bounds.outWidth / sample > 1600 || bounds.outHeight / sample > 1600) sample *= 2
        val bitmap = BitmapFactory.decodeByteArray(raw, 0, raw.size, BitmapFactory.Options().apply { inSampleSize = sample })
            ?: error("Não foi possível abrir a imagem.")
        val orientation = runCatching { ExifInterface(ByteArrayInputStream(raw)).getAttributeInt(
            ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL) }.getOrDefault(ExifInterface.ORIENTATION_NORMAL)
        val degrees = when (orientation) {
            ExifInterface.ORIENTATION_ROTATE_90 -> 90f
            ExifInterface.ORIENTATION_ROTATE_180 -> 180f
            ExifInterface.ORIENTATION_ROTATE_270 -> 270f
            else -> 0f
        }
        val rotated = if (degrees == 0f) bitmap else Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height,
            Matrix().apply { postRotate(degrees) }, true).also { bitmap.recycle() }
        val output = ByteArrayOutputStream()
        try {
            for (quality in listOf(84, 72, 58)) {
                output.reset()
                rotated.compress(Bitmap.CompressFormat.JPEG, quality, output)
                if (output.size() <= 4 * 1024 * 1024) return output.toByteArray()
            }
            error("A foto ficou grande demais. Escolha outra imagem.")
        } finally { rotated.recycle() }
    }
}
