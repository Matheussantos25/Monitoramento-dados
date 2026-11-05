package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@Composable internal fun VocabularyReviewPanel(items:List<PersonalItem>,busy:Boolean,vm:WorkspaceViewModel) {
    var refreshed by remember {mutableIntStateOf(0)}
    val now=remember(items,refreshed){Instant.now().epochSecond}
    val all=items.filter {!it.archived}.mapNotNull {item->vocabularyDocument(item)?.let {Triple(item,it,(it.review ?: VocabularyReview()).normalized())}}
    val ready=all.filter {runCatching {vocabularyCard(it.second)}.isSuccess}
    val due=ready.filter {it.third.due_at<=now}.sortedWith(compareBy<Triple<PersonalItem,Vocabulary,VocabularyReview>> {it.third.reviews==0}.thenBy {it.third.due_at}.thenBy {it.first.id})
    Text("${due.size} para revisar · ${ready.count {it.third.reviews==0}} novos · ${ready.size} no baralho",style=MaterialTheme.typography.titleMedium)
    Text("Leia a frente, tente lembrar e revele a resposta.")
    if(ready.size<all.size)Text("${all.size-ready.size} cartão(ões) aguardando frase, palavra em destaque ou significado em Criar e editar.")
    TextButton({refreshed++;vm.refresh()},enabled=!busy){Text("Atualizar fila")}
    val current=due.firstOrNull()
    if(current==null) {
        Text(if(ready.isEmpty())"Crie seu primeiro cartão em Criar e editar." else "Tudo revisado por enquanto.")
        ready.minOfOrNull {it.third.due_at}?.let {next -> Text("Próxima revisão: "+Instant.ofEpochSecond(next).atZone(ZoneId.of("America/Sao_Paulo")).format(DateTimeFormatter.ofPattern("dd/MM 'às' HH:mm")))}
        return
    }
    val (item,data,state)=current
    var revealed by rememberSaveable(item.id,item.revision) {mutableStateOf(false)}
    val (front,back)=vocabularyCard(data.copy(image=""))
    Panel("FRENTE · lembre do significado") {
        Spacer(Modifier.height(16.dp));VocabularyHtml(front);Spacer(Modifier.height(16.dp))
        if(revealed) {
            HorizontalDivider();Text("VERSO · significado e imagem",style=MaterialTheme.typography.labelLarge)
            VocabularyHtml(back)
            if(data.image.isNotBlank()) {VocabularyImage(data.image,data.word);Text(data.image_credit,style=MaterialTheme.typography.bodySmall)}
        } else Button({revealed=true},Modifier.fillMaxWidth(),enabled=!busy){Text("Mostrar resposta")}
    }
    if(revealed) {
        Text("Errei: não lembrei · Difícil: com esforço · Bom: lembrei · Fácil: imediato",style=MaterialTheme.typography.bodySmall)
        vocabularyRatings.chunked(2).forEach {ratings -> Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            ratings.forEach {rating ->
                val preview=scheduleVocabularyReview(state,rating,now)
                OutlinedButton({
                    val updated=scheduleVocabularyReview(state,rating,Instant.now().epochSecond)
                    vm.save(item.copy(body=vocabularyBody(data.copy(review=updated))),item) {revealed=false;refreshed++}
                },Modifier.weight(1f),enabled=!busy) {Text(rating+" · "+vocabularyInterval(preview.due_at-now))}
            }
        }}
    }
}
