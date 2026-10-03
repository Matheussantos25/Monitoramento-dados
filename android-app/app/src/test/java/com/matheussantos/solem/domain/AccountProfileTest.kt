package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test
import kotlinx.serialization.json.*

class AccountProfileTest {
    private val owner = "msdof25@gmail.com"
    private val cutoff = "2026-10-03T23:00:00Z"
    @Test fun ownerPreserved() {
        assertFalse(genericAccount(" MSDOF25@GMAIL.COM ", null, owner, cutoff))
        assertFalse(genericAccount(owner, "2026-12-01T00:00:00Z", owner, cutoff))
    }
    @Test fun onlyNewAccountsGetGenericDefaults() {
        assertFalse(genericAccount("old@example.test", "2026-10-03T22:59:59Z", owner, cutoff))
        assertTrue(genericAccount("new@example.test", cutoff, owner, cutoff))
        assertTrue(genericAccount("new@example.test", null, owner, cutoff))
        assertTrue(genericAccount("new@example.test", "2026-10-03T20:00:00-03:00", owner, cutoff))
    }
    @Test fun genericCatalogAndPersonalTopicsAreIsolated() {
        val root = Json.parseToJsonElement(javaClass.getResource("/catalog.json")!!.readText()).jsonObject
        val defaults = Json.parseToJsonElement(javaClass.getResource("/account_defaults.json")!!.readText()).jsonObject
        val genericRoot = JsonObject(root + defaults.filterKeys { it in listOf("EXERCICIOS_PRESETADOS", "TOPICOS_EDITAL", "DECKS_ANKI", "FONTES_QUESTOES") } + mapOf(
            "DISCIPLINAS_ESTUDO" to JsonArray(defaults.getValue("TOPICOS_EDITAL").jsonObject.keys.map(::JsonPrimitive))))
        val generic = Catalog(genericRoot, true)
        val old = Catalog(root)
        assertTrue("Mewing com borracha" in old.exercises)
        assertFalse("Mewing com borracha" in generic.exercises)
        assertFalse("Massagem Facial" in generic.exercises)
        assertFalse("FGV" in generic.sources)
        assertTrue("Programação" in generic.subjects)
        val own = generic.withStudyTopics(listOf(com.matheussantos.solem.data.model.TrainingRecord(
            1, "2026-10-04", "12:00:00", "Estudos", "Design", extras=buildJsonObject { put("topico_edital", "Tipografia") })))
        assertEquals(listOf("Tipografia"), own.topics["Design"])
        assertFalse("Design" in old.subjects)
    }
}
