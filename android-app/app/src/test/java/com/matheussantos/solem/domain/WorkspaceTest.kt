package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class WorkspaceTest {
    @Test fun moneyIsExact() {assertEquals(29L,moneyCents("0,29"));assertEquals(12550L,moneyCents("125.50"))}
    @Test fun invalidMoneyIsRejected() {listOf("NaN","-1","1.000,00","1e5","1.234").forEach {assertTrue(runCatching {moneyCents(it)}.isFailure)}}
    @Test fun mindMapParentsAreDeterministic() {
        val nodes=mindNodes("Raiz\n  Um\n    Filho\n  Dois")
        assertEquals(listOf(null,0,1,0),nodes.map{it.parent})
        listOf("","Raiz\nOutra","Raiz\n    Salto","Raiz\n\tTab").forEach {assertTrue(runCatching{mindNodes(it)}.isFailure)}
    }
    @Test fun rejectsNonPdf() {assertTrue(runCatching{validatePdf("<html>".toByteArray())}.isFailure);validatePdf("%PDF-1.7".toByteArray())}
}
