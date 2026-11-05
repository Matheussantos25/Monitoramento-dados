package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.contentDescription
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.matheussantos.solem.data.model.*
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.viewmodel.TrainingViewModel
import java.time.LocalDate
import java.time.LocalTime
import java.time.ZoneOffset

@Composable fun LanguagePage(rows: List<TrainingRecord>, busy: Boolean, vm: TrainingViewModel, workspaceVm: WorkspaceViewModel) {
    var section by rememberSaveable {mutableStateOf("Progresso")}
    var language by rememberSaveable {mutableStateOf("Todos")}
    var day by rememberSaveable {mutableStateOf(today().toString())}
    var period by rememberSaveable {mutableStateOf("Últimos 7 dias")}
    var editing by rememberSaveable {mutableStateOf<Long?>(null)}
    var lastContext by rememberSaveable {mutableStateOf(LanguageEntryContext())}
    var generation by rememberSaveable {mutableIntStateOf(0)}
    val sessions=rows.filter {it.isLanguage()}
    Page("Idiomas") {
        Text("Sua mente em movimento. Anki, séries e prática, no seu ritmo.")
        Row(Modifier.horizontalScroll(rememberScrollState()),horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            listOf("Progresso","Registrar","Histórico","Vocabulário → Anki").forEach {name -> FilterChip(section==name,{section=name;editing=null},label={Text(name)})}
        }
        when(section) {
            "Vocabulário → Anki" -> VocabularyPanel(workspaceVm)
            "Progresso" -> {
                Choice("Idioma do painel",language,listOf("Todos")+sessions.map {it.extra("idioma")}.distinct().sorted()) {language=it}
                Choice("Período do progresso",period,languagePeriods){period=it}
                Field("Data de referência (AAAA-MM-DD)",day) {day=it}
                val parsed=runCatching {LocalDate.parse(day)}.getOrNull()
                if(parsed==null || parsed>today()) Text("Informe uma data válida, até hoje.",color=MaterialTheme.colorScheme.error)
                else {
                    val selected=language.takeUnless {it=="Todos"}
                    val (start,calendarEnd)=languagePeriodBounds(parsed,period)
                    val end=minOf(calendarEnd,today())
                    val range=languageRangeRecords(sessions,start,end,selected)
                    val total=languageRangeTotals(range,start,end,selected)
                    val active=range.map {it.data.take(10)}.distinct().size
                    val dates=DateTimeFormatter.ofPattern("dd/MM/yyyy")
                    Text("${start.format(dates)} a ${end.format(dates)} · $language",style=MaterialTheme.typography.bodyMedium)
                    Panel("Tempo de estudo") {
                        Text("${total.minutes} min",style=MaterialTheme.typography.headlineLarge,color=MaterialTheme.colorScheme.primary)
                        Text("$active / ${ChronoUnit.DAYS.between(start,end)+1} dias de prática · ${total.sessions} sessões")
                        Text("${if(active>0)total.minutes/active else 0} min por dia com prática",style=MaterialTheme.typography.bodySmall)
                    }
                    Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                        LanguageStat("Revisão no Anki","${total.reviewMinutes} min",Modifier.weight(1f))
                        LanguageStat("Cards revisados",total.reviewed.toString(),Modifier.weight(1f))
                    }
                    Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                        LanguageStat("Cards adicionados",total.added.toString(),Modifier.weight(1f))
                        LanguageStat("Episódios / vídeos",total.episodes.toString(),Modifier.weight(1f))
                    }
                    if(total.sessions==0)Text("Nenhuma sessão neste intervalo. Escolha outro período ou registre sua próxima prática.")
                    val unit=if(period=="Dia")"horário" else if(period in listOf("Semestre","Ano"))"mês" else "dia"
                    LanguageRhythm("Seu ritmo por $unit",languageChart(sessions,start,end,period,selected))
                    Text("Tempo informado por você; não é uma avaliação de fluência.",style=MaterialTheme.typography.bodySmall)
                    Button({section="Registrar"},Modifier.fillMaxWidth()) {Text("Registrar prática")}
                }
            }
            "Registrar" -> key(generation) { LanguageEditor(null,busy,vm,rows,initialContext=lastContext,
                onNewSaved={lastContext=it}) {generation++} }
            else -> {
                val old=sessions.firstOrNull {it.id==editing}
                if(old!=null) {
                    TextButton({editing=null}) {Text("Voltar às sessões")}
                    key(old.id) {LanguageEditor(old,busy,vm,rows) {editing=null}}
                } else {
                    var page by rememberSaveable {mutableIntStateOf(0)}
                    val sorted=sessions.sortedWith(compareByDescending<TrainingRecord> {it.data}.thenByDescending {it.horario}.thenByDescending {it.id})
                    val last=((sorted.size-1).coerceAtLeast(0))/10
                    val current=page.coerceAtMost(last)
                    if(sorted.isEmpty()) Text("Nenhuma sessão de idioma registrada. Seus estudos anteriores continuam em Estudar.")
                    sorted.drop(current*10).take(10).forEach {row -> Panel("${row.extra("idioma")} · ${row.extra("atividade_idioma")}") {
                        Text("${row.data} às ${row.horario.take(5)} · ${row.durationMinutes} min")
                        if(row.extra("titulo").isNotBlank()) Text(row.extra("titulo"))
                        if(row.number("episodios")>0) Text("${row.number("episodios").toInt()} episódios/vídeos · Áudio: ${row.extra("idioma_audio")} · Legendas: ${row.extra("legendas")}")
                        if(row.number("cards_adicionados")>0 || row.number("cards_revisados")>0) Text("${row.number("cards_revisados").toInt()} cards revisados · ${row.number("cards_adicionados").toInt()} adicionados")
                        TextButton({editing=row.id},enabled=!busy) {Text("Editar sessão")}
                    } }
                    if(last>0) Row {TextButton({page=current-1},enabled=current>0){Text("Anterior")};Text("${current+1}/${last+1}");TextButton({page=current+1},enabled=current<last){Text("Próxima")}}
                }
            }
        }
    }
}

@Composable fun LanguageEditor(old: TrainingRecord?, busy: Boolean, vm: TrainingViewModel, records: List<TrainingRecord>, initialContext:LanguageEntryContext=LanguageEntryContext(), onNewSaved:(LanguageEntryContext)->Unit={}, done: ()->Unit) {
    var language by rememberSaveable {mutableStateOf(old?.extra("idioma") ?: initialContext.language)}
    var custom by rememberSaveable {mutableStateOf((old?.extra("idioma") ?: initialContext.language).takeUnless {it in languageNames}.orEmpty())}
    var activity by rememberSaveable {mutableStateOf(old?.extra("atividade_idioma") ?: initialContext.activity)}
    var day by rememberSaveable {mutableStateOf(old?.data ?: today().toString())}
    var at by rememberSaveable {mutableStateOf(old?.horario ?: LocalTime.now(ZoneOffset.ofHours(-3)).toString().take(5))}
    var minutes by rememberSaveable {mutableStateOf(old?.durationMinutes?.toString() ?: "20")}
    var title by rememberSaveable {mutableStateOf(old?.extra("titulo") ?: initialContext.title)}
    var reviewed by rememberSaveable {mutableStateOf(old?.number("cards_revisados")?.toInt()?.toString() ?: "0")}
    var added by rememberSaveable {mutableStateOf(old?.number("cards_adicionados")?.toInt()?.toString() ?: "0")}
    var episodes by rememberSaveable {mutableStateOf((old?.number("episodios")?.toInt() ?: 1).coerceAtLeast(1).toString())}
    var audio by rememberSaveable {mutableStateOf(old?.extra("idioma_audio")?.ifBlank {language} ?: initialContext.audio)}
    var subtitles by rememberSaveable {mutableStateOf((old?.extra("legendas") ?: initialContext.subtitles).takeIf {it in subtitleModes} ?: subtitleModes[0])}
    var source by rememberSaveable {mutableStateOf(old?.extra("fonte_idioma") ?: initialContext.source)}
    var contentType by rememberSaveable {mutableStateOf((old?.extra("tipo_conteudo") ?: initialContext.contentType).takeIf {it in contentTypes} ?: contentTypes[0])}
    var notes by rememberSaveable {mutableStateOf(old?.extra("observacoes").orEmpty())}
    var error by remember {mutableStateOf<String?>(null)}
    Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
        Choice("Idioma que estou aprendendo",language.takeIf {it in languageNames} ?: "Outro idioma",languageNames+"Outro idioma") {language=it;audio=it.takeUnless {it=="Outro idioma"} ?: custom}
        if(language !in languageNames) Field("Nome do idioma",custom){custom=it}
        val activityLabels=languageActivities.map {if(it==languageActivities[2])"Série / anime / filme / vídeo" else it}
        Choice("Atividade",activityLabels[languageActivities.indexOf(activity)],activityLabels){
            val next=languageActivities[activityLabels.indexOf(it)]
            if(next!=activity) {activity=next;title="";source="";reviewed="0";added="0";episodes="1";subtitles=if(next=="Escuta") "Sem legenda" else subtitleModes[0]}
        }
        val media=languageMediaActivity(activity)
        if(media) Choice("Tipo de conteúdo",contentType,contentTypes){contentType=it}
        Field("Data da sessão (AAAA-MM-DD)",day){day=it}
        LanguageSuggestField("Horário da sessão",at,timeSuggestions(at),"Digite 22 para ver os horários das 22h; também aceita 2217 ou 22:17."){at=it}
        Field("Tempo efetivo da sessão (min)",minutes,true){minutes=it}
        if(media) {
            val titles=languageMediaTitles(records).filter {it.contains(title,true)}
            LanguageSuggestField(if(activity==languageActivities[2]) "Série, anime, filme ou vídeo" else "Título do conteúdo",title,titles,"Escolha um título do seu histórico ou digite um novo."){title=it.take(160)}
        } else Field(languageMaterialLabel(activity),title){title=it.take(160)}
        if(activity !in languageActivities.take(2)) {
            if(media) LanguageSuggestField("Fonte (opcional)",source,languageSources.filter {it.contains(source,true)},"YouTube, Netflix, Spotify ou outra fonte."){source=it.take(100)}
            else Field("Fonte, plataforma ou professor (opcional)",source){source=it.take(100)}
        }
        if(activity==languageActivities[0]) Field("Cards revisados",reviewed,true){reviewed=it}
        if(activity in languageActivities.take(2)) {
            Field("Cards adicionados ao Anki",added,true){added=it}
            Text("Registro manual. O Solem não acessa sua conta do Anki.",style=MaterialTheme.typography.bodySmall)
        }
        if(media) {
            Field(if(activity==languageActivities[2]) "Episódios / vídeos vistos" else "Conteúdos / episódios ouvidos",episodes,true){episodes=it}
            Text("Informe o tempo total assistido acima: 2 episódios de 25 min = 50 min. Não multiplicaremos novamente.",style=MaterialTheme.typography.bodySmall)
            Field("Idioma do áudio",audio){audio=it}
            if(activity!="Escuta") Choice("Legendas",subtitles,subtitleModes){subtitles=it}
            if(old==null) Text(if(activity=="Escuta") "Escuta é registrada sem legenda. Fonte, título e áudio ficam selecionados após salvar." else "Ao salvar, fonte, título, áudio e legenda ficam selecionados para o próximo episódio.",style=MaterialTheme.typography.bodySmall)
        }
        OutlinedTextField(notes,{notes=it},Modifier.fillMaxWidth(),label={Text("Observações (opcional)")})
        error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
        Button({
            val value=runCatching { languageMutation(day,sessionTime(at),if(language in languageNames) language else custom,activity,minutes.toIntOrNull() ?: -1,
                title,if(activity==languageActivities[0]) reviewed.toIntOrNull() ?: -1 else 0,
                if(activity in languageActivities.take(2)) added.toIntOrNull() ?: -1 else 0,
                if(media) episodes.toIntOrNull() ?: -1 else 0,audio,subtitles,notes,old,source,contentType) }
            value.onSuccess {saved -> error=null;vm.save(old?.id,saved) {if(old==null) onNewSaved(saved.languageEntryContext());done()}}.onFailure {error=it.message ?: "Confira os dados."}
        },enabled=!busy,modifier=Modifier.fillMaxWidth()) {Text(if(busy) "Salvando…" else if(old==null) "Salvar sessão de idioma" else "Salvar alterações")}
    }
}

@Composable private fun LanguageSuggestField(label:String,value:String,options:List<String>,hint:String,change:(String)->Unit) {
    var expanded by remember {mutableStateOf(false)}
    Column(verticalArrangement=Arrangement.spacedBy(4.dp)) {
        OutlinedTextField(value,{change(it);expanded=true},modifier=Modifier.fillMaxWidth().onFocusChanged {expanded=it.isFocused},
            label={Text(label)},singleLine=true,trailingIcon={TextButton({expanded=!expanded}){Text(if(expanded)"Fechar" else "Sugestões")}})
        Text(hint,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
        if(expanded && options.isNotEmpty()) {
            Surface(shape=MaterialTheme.shapes.medium,color=MaterialTheme.colorScheme.surfaceContainer) {
                LazyColumn(Modifier.fillMaxWidth().heightIn(max=180.dp)) {
                    items(options.take(240),key={it}) {option ->
                        ListItem(headlineContent={Text(option)},modifier=Modifier.clickable {change(option);expanded=false})
                    }
                }
            }
        }
    }
}

@Composable private fun LanguageStat(label:String,value:String,modifier:Modifier) {
    Card(modifier) {Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
        Text(label,style=MaterialTheme.typography.labelMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
        Text(value,style=MaterialTheme.typography.headlineSmall)
    }}
}

@Composable private fun LanguageRhythm(title:String,points:List<Pair<String,Double>>) {
    Bars(title,points,"min")
}
