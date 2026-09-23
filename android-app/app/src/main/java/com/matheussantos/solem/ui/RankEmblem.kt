package com.matheussantos.solem.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.R
import com.matheussantos.solem.domain.rankNames

@Composable fun RankEmblem(tier: Int) {
    val images = listOf(R.drawable.rank_0,R.drawable.rank_1,R.drawable.rank_2,R.drawable.rank_3,R.drawable.rank_4,R.drawable.rank_5,R.drawable.rank_6,R.drawable.rank_7)
    if (tier in images.indices) Image(painterResource(images[tier]), "Insígnia ${rankNames[tier]}", Modifier.size(140.dp,100.dp))
}
