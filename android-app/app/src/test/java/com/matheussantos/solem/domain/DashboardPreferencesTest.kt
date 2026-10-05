package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class DashboardPreferencesTest {
    private val day=LocalDate.parse("2026-10-05")
    private fun workout(id:Long,reps:Int)=TrainingRecord(id,day.toString(),"12:00:00","Pernas","Agachamento",repeticoes=reps)
    private fun missions(rows:List<TrainingRecord> = emptyList(),health:List<HealthEntry> = emptyList(),
        available:Boolean=true,settings:DashboardPreferences=DashboardPreferences(),generic:Boolean=false) =
        dailyMissions(rows,health,settings,generic,available,day).associateBy {it.id}

    @Test fun genericDefaultsKeepPrivatePersonalExercisesHidden() {
        val generic=DashboardPreferences.defaults(true)
        assertEquals(10,generic.pushups)
        assertEquals(50,DashboardPreferences.defaults(false).pushups)
        assertFalse(missions(settings=generic,generic=true).containsKey("mewing"))
        assertTrue(missions().containsKey("mewing"))
        assertFalse(missions(settings=generic.copy(hidden=emptySet()),generic=true).containsKey("mewing"))
    }
    @Test fun validationChecksBoundsAndModes() {
        assertEquals("Matheus",DashboardPreferences(nickname=" Matheus ").validated().nickname)
        listOf(DashboardPreferences(waterMl=0),DashboardPreferences(pushups=-1),DashboardPreferences(walkKm=101),
            DashboardPreferences(theme="unknown"),DashboardPreferences(hidden=setOf("unknown"))).forEach {
            assertTrue(runCatching {it.validated()}.isFailure)
        }
    }
    @Test fun sessionsSumOnceAndRespectSelectedDayAndTargets() {
        val first=workout(1,20);val second=workout(2,30)
        val mission=missions(listOf(first,second,first,workout(3,100).copy(data=day.minusDays(1).toString()))) .getValue("agachamento")
        assertEquals(50.0,mission.value!!,0.001)
        assertTrue(mission.complete)
        assertEquals(1f,mission.fraction,0.001f)
        val larger=missions(listOf(first,second),settings=DashboardPreferences(squats=100)).getValue("agachamento")
        assertFalse(larger.complete)
        assertEquals(.5f,larger.fraction,0.001f)
    }
    @Test fun waterUsesOnlyPrivateEntriesOnSelectedDay() {
        val water=HealthEntry("a",day.toString(),"13:00:00","water",buildJsonObject {put("volume_ml",750);put("quantidade",5)})
        val legacy=TrainingRecord(1,day.toString(),"12:00:00","Nutrição","Água",extras=buildJsonObject {put("volume_ml",1000);put("quantidade",2)})
        val result=missions(listOf(legacy),listOf(water,water,water.copy(id="b",day=day.minusDays(1).toString())))
        assertEquals(3750.0,result.getValue("water").value!!,0.001)
        assertTrue(result.getValue("water").complete)
    }
    @Test fun unavailableHealthIsNotZeroOrComplete() {
        val all=missions(available=false,settings=DashboardPreferences(hidden=emptySet()))
        assertNull(all.getValue("water").value)
        assertNull(all.getValue("sleep").value)
        assertFalse(all.getValue("water").complete)
        assertEquals(0f,all.getValue("water").fraction,0.001f)
    }
    @Test fun studyRespectsExactTimeAndExcludesAnkiFromQuestions() {
        val study=TrainingRecord(1,day.toString(),"12:00:00","Estudos","Matemática",durationMinutes=2,
            extras=buildJsonObject {put("q_certas",15);put("q_erradas",5);put("tempo_segundos_exato",90);put("tempo_video",2)})
        val anki=study.copy(id=2,durationMinutes=10,extras=buildJsonObject {put("fonte_questoes","Anki");put("q_certas",100)})
        val result=missions(listOf(study,anki))
        assertEquals(20.0,result.getValue("questions").value!!,0.001)
        assertEquals(13.5,result.getValue("study").value!!,0.001)
    }
    @Test fun corruptNumericExtrasDoNotPoisonProgress() {
        val row=TrainingRecord(1,day.toString(),"12:00:00","Estudos","Estudo",extras=buildJsonObject {
            put("q_certas","NaN");put("q_erradas",-5);put("tempo_segundos_exato","Infinity")
        })
        val result=missions(listOf(row))
        assertEquals(0.0,result.getValue("questions").value!!,0.001)
        assertEquals(0.0,result.getValue("study").value!!,0.001)
        assertEquals(0f,DailyMission("x","x",Double.NaN,10,"rep",1).fraction,0.001f)
    }
    @Test fun firstSyncAndDecreasesDoNotCelebrate() {
        assertNull(journeyPromotion(null,PromotionCheckpoint(12,4)))
        assertNull(journeyPromotion(PromotionCheckpoint(12,4),PromotionCheckpoint(11,3)))
        assertEquals(JourneyPromotion(13,5),journeyPromotion(PromotionCheckpoint(12,4),PromotionCheckpoint(13,5)))
    }
    @Test fun studyPromotionsUsePerTopicBaselines() {
        val before=PromotionCheckpoint(3,2,mapOf("math" to 1,"language" to -1))
        val now=PromotionCheckpoint(3,2,mapOf("math" to 2,"language" to 0,"new" to 7))
        val promotion=journeyPromotion(before,now)!!
        assertEquals(2,promotion.studyTier)
        assertEquals(2,promotion.studyCount)
        assertNull(promotion.physicalTier)
    }
    @Test fun hidingMissionsDoesNotChangeXpRules() {
        val rows=listOf(workout(1,20))
        assertTrue(missions(rows,settings=DashboardPreferences(hidden=missionIds)).isEmpty())
        assertEquals(30,calculateProgress(rows,day).xp)
    }
}
