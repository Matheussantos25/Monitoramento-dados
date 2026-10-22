package com.matheussantos.solem.domain
import com.matheussantos.solem.data.model.PersonalItem
import org.junit.Assert.*
import org.junit.Test
class ScriptDocumentTest {
    @Test fun roundTripAndLegacy() {
        val document=ScriptDocument("script","Olá\n</script> 😀","Descrição","gacha, vídeo")
        val item=PersonalItem("test","note","Título",scriptBody(document))
        validatePersonalItem(item)
        assertEquals(document,scriptDocument(item))
        assertNull(scriptDocument(item.copy(body="Anotação comum")))
        assertNull(scriptDocument(item.copy(body=SCRIPT_PREFIX+"[]")))
        val python=SCRIPT_PREFIX+"""{"type": "idea", "text": "Texto", "description": "Descrição", "tags": "vídeo"}"""
        assertEquals("Descrição",scriptDocument(item.copy(body=python))!!.description)
        assertTrue(runCatching {scriptBody(document.copy(text="a".repeat(40001)))}.isFailure)
    }
}
