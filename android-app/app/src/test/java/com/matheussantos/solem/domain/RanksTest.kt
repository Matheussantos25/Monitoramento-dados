package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.TrainingRecord
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.LocalDate

class RanksTest {
    @Test fun totalRepetitionsAreNotMultipliedAndDuplicatesAreIgnored() {
        val row = TrainingRecord(1, "2026-09-01", "12:00", "Pernas", "Agachamento", series = 10, repeticoes = 100)
        val result = calculateRanks(listOf(row, row, row.copy(id = 2, data = "2099-01-01")), emptyMap(), LocalDate.of(2026, 9, 7))
        assertEquals(100L, result.reps)
        assertEquals(1, result.tier)
    }
    @Test fun accuracyRequiresEvidence() {
        assertEquals(-1, TopicRank("P", "Sintaxe", 19, 19).tier)
        assertEquals(1, TopicRank("P", "Sintaxe", 20, 20).tier)
        assertEquals(7, TopicRank("P", "Sintaxe", 200, 200).tier)
        assertEquals(0, TopicRank("P", "Sintaxe", 0, 20).tier)
    }
}
