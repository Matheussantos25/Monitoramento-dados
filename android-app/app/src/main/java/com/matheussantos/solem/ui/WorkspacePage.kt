package com.matheussantos.solem.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.viewinterop.AndroidView
import android.widget.TextView
import io.noties.markwon.Markwon
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.matheussantos.solem.data.model.PersonalItem
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import java.util.UUID
import java.time.YearMonth

@Composable fun WorkspacePage(vm: WorkspaceViewModel = viewModel(), module: String? = null) {
    val state by vm.state.collectAsStateWithLifecycle()
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var signup by remember { mutableStateOf(false) }
    var search by remember { mutableStateOf("") }
    var archived by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf<PersonalItem?>(null) }
    var creating by remember { mutableStateOf(false) }
    var pending by remember { mutableStateOf<PersonalItem?>(null) }
    var month by remember { mutableStateOf(YearMonth.from(today()).toString()) }
    val upload = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        val item = pending
        if (uri != null && item != null) vm.upload(item,uri)
        pending = null
    }
    val download = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/pdf")) { uri ->
        val item = pending
        if (uri != null && item != null) vm.export(item,uri)
        pending = null
    }
    LaunchedEffect(state.signedIn) { if(!state.signedIn) { editing=null;creating=false;pending=null;search="" } }
    Page(module ?: "✳ solem") {
        Text(if(module==null) "Entre para acessar seu histórico, sua evolução e sua biblioteca pessoal." else "Ideias, referências e próximos passos.")
        if(state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        state.message?.let { Text(it,color=if(state.failed) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary) }
        if (!state.signedIn) {
            Field("E-mail",email) { email=it }
            OutlinedTextField(password,{password=it},Modifier.fillMaxWidth(),label={Text("Senha")},visualTransformation=PasswordVisualTransformation(),singleLine=true)
            Row { Checkbox(signup,{signup=it}); Text("Criar conta") }
            Button({vm.login(email,password,signup);password=""},enabled=!state.busy) { Text("Continuar") }
            Text("Se estiver criando uma conta, confira seu e-mail para confirmar o cadastro.")
        } else {
            if(module == null) {
                Text("Abrindo seu espaço…")
                return@Page
            }
            Row {
                TextButton(vm::refresh,enabled=!state.busy) { Text("Atualizar") }
            }
            Field("Buscar título ou conteúdo",search) {search=it}
            Row { Checkbox(archived,{archived=it;editing=null;creating=false}); Text("Mostrar arquivados") }
            val kind = workspaceKinds.getValue(module)
            if(kind=="plan") {
                Field("Mês (AAAA-MM)",month) {month=it}
                Text("Planejar ou concluir aqui não gera XP. Registre a prática em Treino ou Estudar.")
            }
            val filtered = state.items.filter { it.kind==kind && it.archived==archived && (it.title+" "+it.body).contains(search,true) && (kind!="plan" || it.eventDate.orEmpty().startsWith(month)) }.sortedWith(compareBy({it.eventDate.orEmpty()},{it.eventTime},{it.title}))
            if(kind=="investment") {
                Text("Valores manuais em BRL, sem cotação ao vivo, corretora ou operações. Diferença nominal, não rentabilidade anualizada.")
                val cost=filtered.sumOf {it.investedCents};val value=filtered.sumOf{it.valueCents}
                Panel("Totais da lista filtrada") {Text("Aplicado: R$ %.2f".format(cost/100.0));Text("Saldo informado: R$ %.2f".format(value/100.0));Text("Diferença: R$ %.2f".format((value-cost)/100.0))}
            }
            if(!archived) Button({editing=null;creating=true},enabled=!state.busy) {Text("＋ Nova página")}
            if(creating || editing!=null) {
                key(kind,editing?.id,editing?.revision,creating) {
                    PersonalEditor(kind,editing,state.busy,{editing=null;creating=false}) { value -> vm.save(value,editing) {saved->editing=saved;creating=false} }
                }
                return@Page
            }
            if(filtered.isEmpty()) Text("Nenhum registro neste filtro. Crie um item ou ajuste sua busca.")
            filtered.forEach { item ->
                Panel(item.title) {
                    when(kind) {
                        "plan" -> Text("${item.eventDate} · ${item.eventTime} · ${item.durationMinutes} min · ${if(item.done) "Concluído" else "Planejado"}")
                        "investment" -> Text("Saldo em ${item.eventDate}: R$ %.2f · aplicado: R$ %.2f".format(item.valueCents/100.0,item.investedCents/100.0))
                        "mindmap" -> {
                            val nodes=runCatching{mindNodes(item.body)}.getOrNull()
                            nodes?.forEach {node ->
                                Surface(modifier=Modifier.fillMaxWidth().padding(start=(node.depth*14).dp),color=MaterialTheme.colorScheme.surfaceContainer,shape=MaterialTheme.shapes.small) {
                                    Text((if(node.parent==null) "◈ " else "└─ ")+node.label,Modifier.padding(10.dp))
                                }
                            }
                        }
                        else -> if(item.body.isNotBlank()) Text(item.body.take(150),maxLines=2,overflow=androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                    }
                    Row {
                        if(!archived) TextButton({editing=item;creating=false},enabled=!state.busy) {Text("Abrir página")}
                        TextButton({vm.archive(item);editing=null;creating=false},enabled=!state.busy) {Text(if(archived) "Restaurar" else "Arquivar")}
                    }
                    if(kind=="pdf" && !archived) {
                        Text("Envie o arquivo após criar o registro. Se houve falha de rede, tente exportar antes de reenviar. Arquivos existentes não são sobrescritos.")
                        Button({pending=item;upload.launch(arrayOf("application/pdf"))},enabled=!state.busy) {Text("Selecionar e enviar PDF")}
                        OutlinedButton({pending=item;download.launch("${item.id}.pdf")},enabled=!state.busy) {Text("Exportar PDF privado")}
                        Text("Ao exportar, você cria uma cópia fora da proteção do login do Solem.",style=MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

@Composable private fun PersonalEditor(kind: String, old: PersonalItem?, busy: Boolean, cancel: () -> Unit, save: (PersonalItem) -> Unit) {
    val id=remember {old?.id ?: UUID.randomUUID().toString()}
    var title by remember {mutableStateOf(old?.title.orEmpty())}
    var body by remember {mutableStateOf(old?.body.orEmpty())}
    var day by remember {mutableStateOf(old?.eventDate ?: today().toString())}
    var hour by remember {mutableStateOf(old?.eventTime?.ifBlank{"09:00"} ?: "09:00")}
    var duration by remember {mutableStateOf((old?.durationMinutes ?: 30).toString())}
    var done by remember {mutableStateOf(old?.done ?: false)}
    var invested by remember {mutableStateOf((old?.investedCents ?: 0).toBigDecimal().movePointLeft(2).toPlainString())}
    var value by remember {mutableStateOf((old?.valueCents ?: 0).toBigDecimal().movePointLeft(2).toPlainString())}
    var error by remember {mutableStateOf<String?>(null)}
    Column(verticalArrangement=Arrangement.spacedBy(16.dp)) {
        Text(if(old==null) "Página em branco" else old.title,style=MaterialTheme.typography.headlineMedium)
        Field("Título",title) {title=it.take(160)}
        if(kind=="mindmap") Text("Uma raiz, 2 espaços por nível filho. Até 80 tópicos, 5 níveis e 160 caracteres por tópico. O mapa visual aparece após salvar.")
        var reading by remember(id) { mutableStateOf(false) }
        if(kind in listOf("note","summary")) {
            Row {
                TextButton({reading=false}) {Text(if(!reading) "✓ Editar" else "Editar")}
                TextButton({reading=true}) {Text(if(reading) "✓ Leitura" else "Leitura")}
            }
            Text("Use Markdown para títulos, listas e destaques. Salve para sincronizar.",style=MaterialTheme.typography.bodySmall)
        }
        if(reading) MarkdownDocument(body) else OutlinedTextField(body,{body=it.take(50000)},Modifier.fillMaxWidth().heightIn(min=420.dp),label={Text("Comece a escrever…")},textStyle=MaterialTheme.typography.bodyLarge)
        if(kind in listOf("plan","investment")) Field(if(kind=="plan") "Data (AAAA-MM-DD)" else "Data do saldo (AAAA-MM-DD)",day) {day=it}
        if(kind=="plan") {
            Field("Horário (HH:MM)",hour) {hour=it};Field("Duração em minutos",duration,true) {duration=it}
            Row {Checkbox(done,{done=it});Text("Concluído")}
        }
        if(kind=="investment") {Field("Total aplicado em R$ (sem milhar)",invested,true){invested=it};Field("Saldo informado em R$",value,true){value=it}}
        error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
        Row {
            Button({
                try {
                    val item=PersonalItem(id,kind,title.trim(),body,if(kind in listOf("plan","investment")) day else null,
                        if(kind=="plan") hour else "",if(kind=="plan") duration.toIntOrNull() ?: 0 else 0,done,
                        if(kind=="investment") moneyCents(invested) else 0,if(kind=="investment") moneyCents(value) else 0)
                    validatePersonalItem(item);error=null;save(item)
                } catch(e: IllegalArgumentException) {error=e.message}
            },enabled=!busy) {Text("Salvar")}
            TextButton(cancel,enabled=!busy) {Text("Fechar editor")}
        }
    }
}

@Composable private fun MarkdownDocument(body: String) {
    val context = LocalContext.current
    val renderer = remember(context) { Markwon.create(context) }
    val color = MaterialTheme.colorScheme.onSurface.toArgb()
    AndroidView(
        modifier=Modifier.fillMaxWidth().heightIn(min=300.dp),
        factory={TextView(it).apply {textSize=17f;setTextIsSelectable(true);setLineSpacing(8f,1.15f)}},
        update={it.setTextColor(color);renderer.setMarkdown(it,body.ifBlank {"*Esta página ainda está em branco.*"})}
    )
}
