package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.*
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class LanguagePeriodsTest {
    private fun row(id:Long,day:String,minutes:Int=20,language:String="Inglês",title:String=""):TrainingRecord {
        val m=languageMutation(day,"22:17",language,if(title.isBlank())languageActivities[0] else languageActivities[2],minutes,
            title=title,reviewed=10,episodes=if(title.isBlank())0 else 1,audio=language,subtitles=subtitleModes[0])
        return TrainingRecord(id,m.data,m.horario,m.group,m.exercicio,durationMinutes=m.durationMinutes,extras=m.extras)
    }
    @Test fun calendarBoundaries() {
        assertEquals(LocalDate.of(2024,2,29),languagePeriodBounds(LocalDate.of(2024,2,20),"Mês").second)
        assertEquals(LocalDate.of(2025,12,28),languagePeriodBounds(LocalDate.of(2026,1,3),"Últimos 7 dias").first)
        assertEquals(LocalDate.of(2026,1,1) to LocalDate.of(2026,6,30),languagePeriodBounds(LocalDate.of(2026,6,30),"Semestre"))
        assertEquals(LocalDate.of(2026,7,1) to LocalDate.of(2026,12,31),languagePeriodBounds(LocalDate.of(2026,7,1),"Semestre"))
    }
    @Test fun metricsAndChartAgreeWithoutDuplicatesOrOtherLanguages() {
        val rows=listOf(row(1,"2025-12-31",10),row(2,"2026-01-01",30),row(3,"2026-01-03",40,title="Film"),row(4,"2026-01-03",90,"Espanhol"),row(5,"2026-01-04",50))
        val (start,end)=languagePeriodBounds(LocalDate.of(2026,1,3),"Últimos 7 dias")
        val total=languageRangeTotals(rows+rows[0],start,end,"Inglês")
        assertEquals(LanguageTotals(80,40,20,0,1,3),total)
        val chart=languageChart(rows+rows[0],start,end,"Últimos 7 dias","Inglês")
        assertEquals(80.0,chart.sumOf {it.second},0.0)
        assertEquals("28/12",chart.first().first);assertEquals("03/01",chart.last().first)
        assertEquals(24,languageChart(rows,end,end,"Dia","Inglês").size)
        assertEquals(40.0,languageChart(rows,end,end,"Dia","Inglês")[22].second,0.0)
    }
    @Test fun timeTypingAndPrefixSuggestions() {
        assertEquals("22:00",sessionTime("22"));assertEquals("22:17",sessionTime("2217"))
        assertEquals("09:03",sessionTime("9:03"));assertEquals("08:15:30",sessionTime("08:15:30"))
        assertEquals(60,timeSuggestions("22").size)
        assertTrue(timeSuggestions("22").all {it.startsWith("22:")})
        assertEquals(10,timeSuggestions("221").size)
        listOf("24","24:00","22:60","abc","").forEach {v ->assertTrue(runCatching {sessionTime(v)}.isFailure)}
    }
    @Test fun titleSuggestionsUseMediaHistoryOnly() {
        val rows=listOf(row(1,"2026-01-01",title="Frieren"),row(2,"2026-01-02",title=" frieren "),row(3,"2026-01-03",title="Arrival"),row(4,"2026-01-04"))
        assertEquals(listOf("Arrival","frieren"),languageMediaTitles(rows))
        assertTrue(languageMediaTitles(emptyList()).isEmpty())
    }
}
