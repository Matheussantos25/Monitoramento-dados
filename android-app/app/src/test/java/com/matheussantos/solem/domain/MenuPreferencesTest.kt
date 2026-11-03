package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test
import kotlinx.serialization.json.*

class MenuPreferencesTest {
    @Test fun defaultsPreserveExistingAndPinRecovery() {
        assertEquals(menuTabIds.toSet(),menuTabs(null,false))
        assertFalse("finance" in menuTabs(null,true))
        assertTrue("finance" in menuTabs(listOf("finance"),true))
        assertEquals(pinnedTabs,menuTabs(emptyList(),true))
        assertFalse("unknown" in menuTabs(listOf("unknown"),false))
        assertEquals(androidTabIds.size,androidTabIds.distinct().size)
    }
    @Test fun editingAndroidPreservesWebOnlyChoices() {
        val changed=mergedMenuTabs(setOf("languages"),menuTabIds.toSet(),androidTabIds.toSet()-pinnedTabs)
        assertTrue("publications" in changed)
        assertTrue(changed.containsAll(pinnedTabs))
        assertFalse("training" in changed)
        assertTrue("languages" in changed)
    }
    @Test fun listeningIsMediaWithoutAnkiCounts() {
        val value=languageMutation("2026-11-03","22:00","Inglês","Escuta",25,
            title="Meu anime",reviewed=20,added=10,episodes=1,audio="Inglês",subtitles="Sem legenda",source="YouTube",contentType="Anime")
        assertEquals(JsonPrimitive(0),value.extras["cards_revisados"])
        assertEquals(JsonPrimitive(0),value.extras["cards_adicionados"])
        assertEquals(JsonPrimitive(1),value.extras["episodios"])
        assertEquals(JsonPrimitive("YouTube"),value.extras["fonte_idioma"])
        assertEquals(JsonPrimitive("Anime"),value.extras["tipo_conteudo"])
        assertFalse(languageMaterialLabel("Leitura").contains("Anki"))
    }
}
