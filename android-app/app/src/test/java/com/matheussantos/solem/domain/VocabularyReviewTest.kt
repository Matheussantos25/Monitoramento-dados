package com.matheussantos.solem.domain
import com.matheussantos.solem.data.model.PersonalItem
import org.junit.Assert.*
import org.junit.Test

class VocabularyReviewTest {
    private val now=1793793600L
    @Test fun stepsAndGrowthMatchWebSchedule() {
        assertEquals(listOf(60L,300L,600L,345600L),vocabularyRatings.map {scheduleVocabularyReview(null,it,now).due_at-now})
        val learning=scheduleVocabularyReview(null,"Bom",now)
        assertThrows(IllegalArgumentException::class.java){scheduleVocabularyReview(learning,"Fácil",now)}
        val mature=scheduleVocabularyReview(learning,"Bom",now+600)
        assertEquals(1,mature.interval_days);assertEquals(2,mature.reviews)
        val state=mature.copy(interval_days=10,due_at=now)
        assertEquals(listOf(12,25,33),listOf("Difícil","Bom","Fácil").map {scheduleVocabularyReview(state,it,now).interval_days})
        val failed=scheduleVocabularyReview(state,"Errei",now)
        assertEquals(1,failed.lapses);assertEquals(0,failed.interval_days);assertEquals(now+60,failed.due_at)
    }
    @Test fun editingContentPreservesScheduleAndLegacyCardsRemainReadable() {
        val old=Vocabulary(word="notice",sentence="I notice the sky.",definition="To become aware.")
        val schedule=scheduleVocabularyReview(null,"Fácil",now)
        val item=PersonalItem("card-one","note","notice",vocabularyBody(old.copy(review=schedule)))
        val restored=vocabularyDocument(item)!!
        assertEquals(schedule,restored.review)
        assertEquals(schedule,vocabularyDocument(item.copy(body=vocabularyBody(restored.copy(definition="Edited."))))!!.review)
        assertNull(vocabularyDocument(item.copy(body=vocabularyBody(old)))!!.review)
        val (front,back)=vocabularyCard(old)
        assertTrue(front.contains("<b>notice</b>"));assertFalse(back.contains("sky"));assertTrue(back.contains("aware"))
    }
}
