package com.matheussantos.solem.ui

import android.animation.ValueAnimator
import android.media.AudioManager
import android.media.ToneGenerator
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import com.matheussantos.solem.data.PersonalizationStore
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.ui.theme.LocalDashboardPreferences
import kotlinx.coroutines.delay

/** First sync is a baseline. Persistent high-water marks prevent repeat celebrations after edits. */
@Composable fun JourneyPromotionHost(rows:List<TrainingRecord>,catalog:Catalog,available:Boolean,store:PersonalizationStore) {
    val preferences=LocalDashboardPreferences.current
    var promotion by remember { mutableStateOf<JourneyPromotion?>(null) }
    val checkpoint=remember(rows,catalog.topics,available) {
        if(available) {
            val ranks=calculateRanks(rows,catalog.topics,today())
            PromotionCheckpoint(calculateProgress(rows).xp / 250 + 1,ranks.tier,
                ranks.topics.associate {"${it.subject}\u001f${it.topic}" to it.tier})
        } else null
    }
    LaunchedEffect(checkpoint) {
        checkpoint?.let { current ->
            val next=journeyPromotion(store.checkpoint(),current)
            store.recordCheckpoint(current)
            if(next!=null) promotion=next
        }
    }
    LaunchedEffect(promotion) {
        if(promotion!=null) {
            if(preferences.sound) {
                val tone=runCatching { ToneGenerator(AudioManager.STREAM_MUSIC,38) }.getOrNull()
                try {
                    tone?.startTone(ToneGenerator.TONE_PROP_BEEP2,180);delay(210)
                    tone?.startTone(ToneGenerator.TONE_PROP_ACK,520);delay(560)
                } finally { tone?.release() }
            }
            delay(4500);promotion=null
        }
    }
    promotion?.let { current ->
        Dialog(onDismissRequest={promotion=null}) {
            var entered by remember { mutableStateOf(false) }
            LaunchedEffect(Unit) { entered=true }
            val duration=if(preferences.motion && ValueAnimator.areAnimatorsEnabled()) 650 else 0
            val scale by animateFloatAsState(if(entered) 1f else .84f,tween(duration),label="promotionScale")
            val alpha by animateFloatAsState(if(entered) 1f else 0f,tween(duration),label="promotionAlpha")
            Card(Modifier.fillMaxWidth().graphicsLayer {scaleX=scale;scaleY=scale;this.alpha=alpha},shape=MaterialTheme.shapes.extraLarge,
                colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.surfaceContainerHigh)) {
                Column(Modifier.padding(28.dp),horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.spacedBy(12.dp)) {
                    Text("NOVA CONQUISTA",style=MaterialTheme.typography.labelLarge,color=MaterialTheme.colorScheme.primary)
                    current.physicalTier?.let { tier -> RankEmblem(tier);Text(rankNames[tier],style=MaterialTheme.typography.headlineLarge) }
                    current.studyTier?.let { tier ->
                        if(current.physicalTier==null) RankEmblem(tier)
                        Text("Estudo · ${rankNames[tier]}",style=MaterialTheme.typography.titleLarge)
                        Text("${current.studyCount} tópico(s) subiram de elo",style=MaterialTheme.typography.bodyMedium)
                    }
                    current.level?.let { level -> Text("Nível $level",style=MaterialTheme.typography.headlineMedium) }
                    Text("Seu progresso veio dos seus registros. Continue no seu ritmo.",style=MaterialTheme.typography.bodyMedium)
                    FilledTonalButton({promotion=null},modifier=Modifier.fillMaxWidth()) {Text("Continuar jornada")}
                }
            }
        }
    }
}
