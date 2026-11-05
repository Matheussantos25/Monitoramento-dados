package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.*
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class LanguagesTest {
    @Test fun nextEpisodeRetainsContextWithoutCopyingSessionMeasurements() {
        val first=languageMutation("2026-11-03","22:15","Espanhol","Escuta",45,
            title="Minha série",episodes=2,audio="Japonês",subtitles="Em português",
            source="YouTube",contentType="Anime",notes="Só este episódio")
        val context=first.languageEntryContext()
        // rememberSaveable uses this same Serializable context across recreation.
        val bytes=java.io.ByteArrayOutputStream()
        java.io.ObjectOutputStream(bytes).use {it.writeObject(context)}
        val restored=java.io.ObjectInputStream(java.io.ByteArrayInputStream(bytes.toByteArray())).use {it.readObject() as LanguageEntryContext}
        assertEquals(context,restored)
        assertEquals(LanguageEntryContext("Escuta","Espanhol","Minha série","YouTube","Anime","Japonês","Sem legenda"),restored)
        val next=languageMutation("2026-11-03","23:00",restored.language,restored.activity,20,
            title=restored.title,episodes=1,audio=restored.audio,subtitles=restored.subtitles,
            source=restored.source,contentType=restored.contentType)
        assertEquals(context,next.languageEntryContext())
        assertEquals(20,next.durationMinutes)
        assertEquals(JsonPrimitive(1),next.extras["episodios"])
        assertEquals(JsonPrimitive(""),next.extras["observacoes"])
        assertEquals(JsonPrimitive(2),first.extras["episodios"])
        assertEquals(45,first.durationMinutes)
    }
    private val day=LocalDate.of(2026,11,1)
    private fun record(id:Long,m:TrainingMutation)=TrainingRecord(id,m.data,m.horario,m.group,m.exercicio,durationMinutes=m.durationMinutes,extras=m.extras)
    @Test fun totalTimeAndCardsDoNotBecomeQuestions() {
        val anki=record(1,languageMutation(day.toString(),"10:30","Inglês",languageActivities[0],20,reviewed=40,added=5))
        val media=record(2,languageMutation(day.toString(),"11:30","Inglês",languageActivities[2],50,title="Série",episodes=2,audio="Inglês",subtitles="Sem legenda"))
        val other=record(3,languageMutation(day.toString(),"12:30","Espanhol","Leitura",15))
        val total=languageTotals(listOf(anki,media,other,anki),day,"Inglês")
        assertEquals(LanguageTotals(70,20,40,5,2,2),total)
        assertEquals(0,anki.repeticoes);assertEquals(0.0,media.number("tempo_video"),0.0)
        assertEquals(30,calculateProgress(listOf(anki,media),day).xp)
        assertEquals(0,languageTotals(listOf(anki),day.minusDays(1)).minutes)
    }
    @Test fun changingActivityClearsPreviousCounters() {
        val value=languageMutation(day.toString(),"10:00","Espanhol","Leitura",30,reviewed=10,added=4,episodes=2)
        assertEquals(JsonPrimitive(0),value.extras["cards_revisados"])
        assertEquals(JsonPrimitive(0),value.extras["cards_adicionados"])
        assertEquals(JsonPrimitive(0),value.extras["episodios"])
    }
    @Test fun validatesSession() {
        assertThrows(IllegalArgumentException::class.java) {languageMutation(day.toString(),"10:00","Inglês","Leitura",0)}
        assertThrows(IllegalArgumentException::class.java) {languageMutation(day.toString(),"10:00","Inglês",languageActivities[2],20)}
        assertThrows(IllegalArgumentException::class.java) {languageMutation(day.toString(),"10:00","Inglês",languageActivities[0],20,added=-1)}
        assertTrue(fitnessPage(19))
    }
}
