package com.matheussantos.solem.ui

import android.app.Activity
import android.content.Intent
import android.speech.RecognizerIntent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import com.matheussantos.solem.domain.VoiceDraft

@Composable fun VoiceInput(example: String, busy: Boolean = false, parse: (String) -> VoiceDraft, apply: (VoiceDraft) -> Unit) {
    var expanded by rememberSaveable { mutableStateOf(false) }
    var text by rememberSaveable { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var draft by remember { mutableStateOf<VoiceDraft?>(null) }
    var waiting by rememberSaveable { mutableStateOf(false) }
    val latestBusy by rememberUpdatedState(busy)
    val launcher=rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        waiting=false
        if(result.resultCode==Activity.RESULT_OK) {
            val spoken=result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)?.firstOrNull()
            if(!spoken.isNullOrBlank()) {text=spoken.take(2000);draft=null;error=null}
            else error="Nenhuma fala recebida. Tente novamente ou use o microfone do teclado."
        } else error="Ditado cancelado. Seus campos continuam como estavam."
    }
    TextButton(onClick={expanded=!expanded}) {Text(if(expanded) "Ocultar entrada por voz" else "🎙 Preencher por voz")}
    if(expanded) Panel("Fale, confira e preencha") {
        Text("Sem API paga do Solem. O serviço de voz do celular pode processar o áudio e precisar de internet. Só escuta quando você toca em Falar; o Solem não guarda o áudio.",style=MaterialTheme.typography.bodySmall)
        Text("Exemplo: $example",style=MaterialTheme.typography.bodySmall)
        Text("Preenche este formulário na data selecionada. Ainda será necessário salvar.",style=MaterialTheme.typography.bodySmall)
        Button(onClick={
            error=null
            try {
                val intent=Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH)
                    .putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    .putExtra(RecognizerIntent.EXTRA_LANGUAGE,"pt-BR")
                    .putExtra(RecognizerIntent.EXTRA_PROMPT,"Fale todos os alimentos e leituras da balança, ou os dados deste formulário")
                    .putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1)
                waiting=true;launcher.launch(intent)
            } catch(_: Exception) {waiting=false;error="Reconhecimento de voz indisponível. Use o microfone do teclado no campo abaixo ou digite."}
        },enabled=!busy && !waiting) {Text(if(waiting) "Aguardando fala…" else "🎙 Falar")}
        Field("O que você falou · pode corrigir",text){text=it.take(2000);draft=null;error=null}
        Button(onClick={try {draft=parse(text);error=null}catch(e:IllegalArgumentException){draft=null;error=e.message}},enabled=!busy && text.isNotBlank()) {Text("Conferir o que entendeu")}
        error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
        draft?.let {value->
            Text(value.preview)
            Button(onClick={if(!latestBusy){apply(value);draft=null}},enabled=!busy) {Text("Preencher campos")}
        }
    }
}
