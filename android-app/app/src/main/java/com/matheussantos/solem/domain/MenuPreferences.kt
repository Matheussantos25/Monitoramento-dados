package com.matheussantos.solem.domain

/** Stable cross-platform IDs, independent of navigation indices. Never an access-control list. */
val menuTabIds = listOf("overview","training","physical","health","study","study_progress","prompts","notes","summaries","pdfs","mindmaps","schedule","finance","publications","settings","account","scripts","languages","weight","history","calendar","ranks")
val pinnedTabs = setOf("overview","settings","account")
val starterTabs = setOf("overview","training","physical","health","languages","settings","account","weight","history","calendar","ranks")
val androidTabIds = listOf("overview","training","physical","health","weight","study","study_progress","prompts","history","calendar","ranks","notes","summaries","pdfs","mindmaps","schedule","finance","settings","scripts","languages")
fun menuTabs(saved:List<String>?,generic:Boolean):Set<String> = if(saved==null) {
    if(generic) starterTabs else menuTabIds.toSet()
} else (saved.filter {it in menuTabIds}+pinnedTabs).toSet()
fun mergedMenuTabs(selected:Set<String>,current:Set<String>,offered:Set<String>):List<String> =
    menuTabIds.filter {it in pinnedTabs || it in selected || (it in current && it !in offered)}
