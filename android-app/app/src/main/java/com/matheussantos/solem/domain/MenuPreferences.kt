package com.matheussantos.solem.domain

/** Stable cross-platform IDs, independent of navigation indices. Never an access-control list. */
val menuTabIds = listOf("overview","training","physical","health","study","study_progress","prompts","notes","summaries","pdfs","mindmaps","schedule","finance","publications","settings","account","scripts","languages","weight","history","calendar","ranks")
val pinnedTabs = setOf("overview","settings","account")
val starterTabs = setOf("overview","training","physical","health","languages","settings","account","weight","history","calendar","ranks")
val androidTabIds = listOf("overview","training","physical","health","weight","study","study_progress","prompts","history","calendar","ranks","notes","summaries","pdfs","mindmaps","schedule","finance","settings","scripts","languages")
val nestedTabs = mapOf("physical" to "training", "study_progress" to "study")
fun menuTabs(saved:List<String>?,generic:Boolean):Set<String> {
    val enabled = saved ?: if(generic) starterTabs.toList() else menuTabIds
    return (enabled.filter {it in menuTabIds}.map {nestedTabs[it] ?: it}+pinnedTabs).toSet()
}
fun mergedMenuTabs(selected:Set<String>,current:Set<String>,offered:Set<String>):List<String> =
    menuTabIds.filter {it !in nestedTabs && (it in pinnedTabs || it in selected || (it in current && it !in offered))}
