package com.matheussantos.solem.domain
import com.matheussantos.solem.data.model.PersonalItem
import org.junit.Assert.*
import org.junit.Test
import java.util.UUID
import kotlinx.serialization.json.*

class NotesTest {
 @Test fun legacyProjectionAndInlineRoundTrip() {
  val id=UUID.randomUUID().toString()
  val ref=UUID.randomUUID().toString()
  val note=PersonalItem(id,"note","Antiga","Texto original")
  val image=PersonalItem(ref,"note","Foto",NOTE_MATERIAL_PREFIX+buildJsonObject {
   put("folder",id);put("type","image");put("value","/9h0ZXN0")
  })
  assertEquals(listOf("text","image"),noteDocument(note,listOf(image)).blocks.map {it.type})
  val blocks=listOf(NoteBlock("a","text","Antes"),NoteBlock("b","image",ref=ref),NoteBlock("c","text","Depois"))
  val event=NoteEditorEvent("save","e","Página",blocks,mapOf(ref to "/9h0ZXN0"))
  val (saved,assets)=prepareNote(id,"",event,emptyList())
  assertEquals(blocks,noteDocument(saved,assets).blocks)
  assertEquals(ref,assets.single().id)
  assertEquals(1,noteDocument(note,assets).blocks.size)
  assertTrue(prepareNote(id,"",event,assets).second.isEmpty())
  assertEquals("Texto original",note.body)
 }
 @Test fun archivedFolderCannotReceiveNotes() {
  val folder=PersonalItem(UUID.randomUUID().toString(),"note","Pasta",NOTE_FOLDER_PREFIX+"{}",archived=true)
  val event=NoteEditorEvent("save","e","Página",emptyList(),emptyMap())
  assertThrows(IllegalArgumentException::class.java) {
   prepareNote(UUID.randomUUID().toString(),folder.id,event,listOf(folder))
  }
 }
}
