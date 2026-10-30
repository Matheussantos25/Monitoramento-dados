package com.matheussantos.solem.domain

import org.junit.Test
import org.junit.Assert.*
import com.matheussantos.solem.data.model.TrainingRecord
import java.time.LocalDate

class ExperienceTest {
    @Test fun linksRestrictSchemeHostAndCredentials() {
        assertTrue(validMotivationLink("https://open.spotify.com/playlist/example"))
        assertTrue(validMotivationLink("https://youtu.be/example"))
        listOf("javascript:alert(1)","http://youtube.com/","https://youtube.com.evil.test/", "https://u:p@youtube.com/","https://127.0.0.1/","https://youtube.com:999/").forEach {assertFalse(validMotivationLink(it))}
    }
    @Test fun comfortDoesNotChangeTargetsOrHistoryPreferences() {
        val old=DashboardPreferences(pushups=100,squats=100)
        val changed=old.copy(comfort=true,contrast=true,largeText=true).validated()
        assertEquals(old.pushups,changed.pushups);assertEquals(old.hidden,changed.hidden)
        assertTrue(old.motion);assertTrue(old.sound)
    }
    @Test fun rhythmCountsSessionsNotRepetitionsAndIgnoresDuplicatesFutureEmpty() {
        val day=LocalDate.of(2026,10,30)
        val row=TrainingRecord(id=1,data=day.toString(),horario="12:00",group="Pernas",exercicio="Agachamento",repeticoes=20)
        val rows=listOf(row,row,row.copy(id=2,data="2026-10-31"),row.copy(id=3,repeticoes=0))
        val result=workoutRhythm(rows,day)
        assertEquals(7,result.size);assertEquals(1,result.sumOf {it.sessions});assertEquals(20,result.last().reps)
    }
}
