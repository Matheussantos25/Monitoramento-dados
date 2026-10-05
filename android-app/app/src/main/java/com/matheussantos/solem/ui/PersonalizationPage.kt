package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.PersonalizationStore
import com.matheussantos.solem.domain.*

@Composable fun PersonalizationPage(store: PersonalizationStore, generic: Boolean) {
    val saved by store.state.collectAsState()
    var draft by remember(saved) { mutableStateOf(saved) }
    var goals by remember(saved) { mutableStateOf(mapOf(
        "water" to saved.waterMl.toString(), "flexao" to saved.pushups.toString(),
        "agachamento" to saved.squats.toString(), "walk" to saved.walkKm.toString(),
        "questions" to saved.questions.toString(), "study" to saved.studyMinutes.toString(),
        "mewing" to saved.mewing.toString(), "sleep" to saved.sleepMinutes.toString())) }
    var feedback by remember { mutableStateOf<String?>(null) }
    var reset by remember { mutableStateOf(false) }
    Page("Do seu jeito") {
        Text("Personalize sua jornada. Estas preferências ficam nesta conta, neste aparelho; não alteram seus registros nem as regras dos elos.", color=MaterialTheme.colorScheme.onSurfaceVariant)
        Panel("Aparência") {
            Field("Como quer ser chamado?", draft.nickname) { draft=draft.copy(nickname=it.take(40)); feedback=null }
            Choice("Tema",draft.theme,listOf("Escuro","Claro","Sistema")) { draft=draft.copy(theme=it) }
            Choice("Cor de destaque",draft.accent,listOf("Glacial","Âmbar","Rubi")) { draft=draft.copy(accent=it) }
            PreferenceSwitch("Celebrar promoções", "Animação ao subir de nível ou elo",draft.motion) { draft=draft.copy(motion=it) }
            PreferenceSwitch("Som de promoção", "Respeita o volume de mídia do aparelho",draft.sound) { draft=draft.copy(sound=it) }
        }
        Panel("Tela inicial") {
            PreferenceSwitch("Ritmo da semana", "Seus dias de estudo e treino",draft.showWeek) { draft=draft.copy(showWeek=it) }
            PreferenceSwitch("Atividades recentes", "As últimas sessões do seu histórico",draft.showRecent) { draft=draft.copy(showRecent=it) }
        }
        Panel("Suas missões diárias") {
            Text("Ative só o que faz sentido para você. Metas são pessoais, não uma prescrição de saúde. Descanso não tira XP.",color=MaterialTheme.colorScheme.onSurfaceVariant)
            val labels=listOf("water" to "Água · ml (250–10.000)", "flexao" to "Flexões · rep (1–10.000)",
                "agachamento" to "Agachamentos · rep (1–10.000)","walk" to "Caminhada/corrida · km (1–100)",
                "questions" to "Questões (1–5.000)","study" to "Estudo · min (1–1.440)",
                "mewing" to "Mewing · rep (1–10.000)","sleep" to "Sono · min (1–960)")
            labels.filter { !generic || it.first!="mewing" }.forEach { (id,label) ->
                Row(verticalAlignment=Alignment.CenterVertically) {
                    Checkbox(checked=id !in draft.hidden,onCheckedChange={enabled -> draft=draft.copy(hidden=if(enabled) draft.hidden-id else draft.hidden+id)})
                    OutlinedTextField(value=goals.getValue(id),onValueChange={goals=goals+(id to it.filter(Char::isDigit).take(5));feedback=null},
                        label={Text(label)},singleLine=true,enabled=id !in draft.hidden,
                        keyboardOptions=androidx.compose.foundation.text.KeyboardOptions(keyboardType=androidx.compose.ui.text.input.KeyboardType.Number),modifier=Modifier.weight(1f))
                }
            }
        }
        feedback?.let { Text(it,color=if(it.startsWith("Salvo")) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error) }
        Button(onClick={
            val result=runCatching {
                fun goal(id:String)=goals.getValue(id).toInt()
                draft.copy(waterMl=goal("water"),pushups=goal("flexao"),squats=goal("agachamento"),walkKm=goal("walk"),
                    questions=goal("questions"),studyMinutes=goal("study"),mewing=goal("mewing"),sleepMinutes=goal("sleep")).validated()
            }
            result.fold(onSuccess={store.save(it);feedback="Salvo. Sua jornada está personalizada."},
                onFailure={feedback="Confira os valores e os limites indicados em cada meta."})
        },modifier=Modifier.fillMaxWidth().heightIn(min=52.dp)) { Text("Salvar personalização") }
        TextButton(onClick={reset=true},modifier=Modifier.fillMaxWidth()) { Text("Restaurar preferências padrão") }
    }
    if(reset) AlertDialog(onDismissRequest={reset=false},title={Text("Restaurar preferências?")},
        text={Text("Só o tema, as metas e a apresentação serão restaurados. Nenhum registro será excluído.")},
        confirmButton={TextButton({store.reset();feedback="Salvo. Preferências padrão restauradas.";reset=false}) {Text("Restaurar")}},
        dismissButton={TextButton({reset=false}) {Text("Cancelar")}})
}

@Composable private fun PreferenceSwitch(title:String,description:String,checked:Boolean,onChange:(Boolean)->Unit) {
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
        Column(Modifier.weight(1f)) {
            Text(title,style=MaterialTheme.typography.titleSmall)
            Text(description,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Switch(checked=checked,onCheckedChange=onChange)
    }
}
