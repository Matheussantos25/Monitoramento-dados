package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.PersonalItem
import org.junit.Assert.*
import org.junit.Test

class VocabularyTest {
    @Test fun crossPlatformPrivateDocumentRoundTrip() {
        val data=Vocabulary("run","I run every day.","To move quickly on foot.","Episode 2")
        val item=PersonalItem("id","note","run",vocabularyBody(data))
        assertEquals(data,vocabularyDocument(item))
        assertNull(vocabularyDocument(item.copy(body="legacy note")))
        assertNull(vocabularyDocument(item.copy(body=VOCAB_PREFIX+"[]")))
        assertTrue(item.body.startsWith("SOLEM_VOCAB_V1\n"))
    }
    @Test fun escapedCardsMatchWholeWordsOnly() {
        val front=vocabularyFront("Run, don't outrun me. I run.","run")
        assertEquals(2,Regex("<b>").findAll(front).count())
        assertTrue(front.contains("outrun"))
        assertTrue(vocabularyFront("She ran home.","run","ran\nrunning").contains("<b>ran</b>"))
        val pair=vocabularyCard(Vocabulary("a+b","Use a+b <script>x</script>","<img src=x onerror=x>"))
        assertTrue(pair.first.contains("<b>a+b</b>"))
        assertFalse(pair.first.contains("<script>"))
        assertFalse(pair.second.contains("<img src=x"))
    }
    @Test fun incompleteCardCanSaveButCannotExport() {
        assertTrue(vocabularyBody(Vocabulary(word="stumble")).isNotBlank())
        assertTrue(runCatching {vocabularyCard(Vocabulary(word="stumble"))}.isFailure)
        assertTrue(runCatching {vocabularyCard(Vocabulary("run","I walk.","Move quickly."))}.isFailure)
    }
    @Test fun mediaHostsAndExportEscaping() {
        assertFalse(vocabularyMediaUrl("https://upload.wikimedia.org.evil.com/a.jpg"))
        assertFalse(vocabularyMediaUrl("https://user@upload.wikimedia.org/a.jpg"))
        assertFalse(vocabularyMediaUrl("http://upload.wikimedia.org/a.jpg"))
        assertTrue(vocabularyMediaUrl("https://thumb.wikimedia.org/a.jpg"))
        val text=vocabularyAnkiText(Vocabulary("run","I run.","A \"quote\"\nnext line"))
        assertTrue(text.startsWith("#separator:Tab\n#html:true"))
        assertTrue(text.contains("&quot;quote&quot;<br>next line"))
    }
}
