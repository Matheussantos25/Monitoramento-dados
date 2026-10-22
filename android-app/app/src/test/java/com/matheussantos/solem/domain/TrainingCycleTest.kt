package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import kotlinx.serialization.json.*
import org.junit.Assert.*
import org.junit.Test
import java.time.LocalDate

class TrainingCycleTest {
    private val definition=Json.decodeFromString<WeeklyPlanDefinition>(javaClass.getResource("/weekly_training_plan.json")!!.readText())
    @Test fun pythonParityForAllCyclePhasesAndBaseGoals() {
        val fixtures=Json.parseToJsonElement(javaClass.getResource("/training_cycle_parity.json")!!.readText()).jsonArray
        fixtures.forEach {element ->
            val case=element.jsonObject
            val name=case.getValue("name").jsonPrimitive.content
            val rows=Json.decodeFromJsonElement<List<TrainingRecord>>(case.getValue("records"))
            val day=LocalDate.parse(case.getValue("day").jsonPrimitive.content)
            val expected=case.getValue("expected").jsonObject
            val plan=weeklyPlanDay(rows,day,definition)
            assertEquals(name,expected.getValue("active").jsonPrimitive.boolean,plan.active)
            assertEquals(name,expected.getValue("stage").jsonPrimitive.int,plan.stage)
            assertEquals(name,expected.getValue("week").jsonPrimitive.int,plan.cycleWeek)
            assertEquals(name,expected.getValue("held").jsonPrimitive.boolean,plan.held)
            assertEquals(name,expected.getValue("completed").jsonPrimitive.boolean,plan.completed)
            assertEquals(name,expected.getValue("recovery").jsonPrimitive.boolean,plan.recovery)
            assertEquals(name,expected["percent"]?.jsonPrimitive?.intOrNull,plan.percent)
            val goals=expected.getValue("goals").jsonArray
            assertEquals(name,goals.size,plan.goals.size)
            goals.zip(plan.goals).forEach {(raw,actual) ->
                val goal=raw.jsonObject
                assertEquals(name,goal.getValue("exercise").jsonPrimitive.content,actual.spec.exercise)
                assertEquals(name,goal.getValue("target").jsonPrimitive.int,actual.target)
                assertEquals(name,goal.getValue("sets").jsonPrimitive.int,actual.spec.sets)
                assertEquals(name,goal.getValue("value").jsonPrimitive.double,actual.value,1e-6)
                assertEquals(name,goal.getValue("unit").jsonPrimitive.content,actual.spec.unit)
            }
            val settings=DashboardPreferences(pushups=100,squats=100)
            val missions=dailyMissions(rows,emptyList(),settings,false,false,day,definition).filter {it.destination==1}
            val base=expected.getValue("base").jsonArray
            assertEquals(name,base.size,missions.size)
            base.zip(missions).forEach {(raw,actual) ->
                val goal=raw.jsonObject
                assertEquals(name,goal.getValue("exercise").jsonPrimitive.content,actual.exercise)
                assertEquals(name,goal.getValue("target").jsonPrimitive.int,actual.target)
                assertEquals(name,goal.getValue("value").jsonPrimitive.double,actual.value!!,1e-6)
            }
            assertEquals(100,settings.pushups)
        }
    }
    @Test fun genericAndHistoricalGoalsUnchanged() {
        val settings=DashboardPreferences.defaults(true)
        val historical=LocalDate.of(2026,10,19)
        assertFalse(weeklyPlanDay(emptyList(),historical,definition).cycle)
        val date=LocalDate.of(2026,10,23)
        assertEquals(dailyMissions(emptyList(),emptyList(),settings,true,false,date),
            dailyMissions(emptyList(),emptyList(),settings,true,false,date,definition))
        assertFalse(weeklyPlanDay(emptyList(),date,definition,false).cycle)
    }
}
