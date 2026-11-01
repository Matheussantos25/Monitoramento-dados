package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
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
    var editing by rememberSaveable {mutableStateOf<Long?>(null)}
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
                Field("Dia do progresso (AAAA-MM-DD)",day) {day=it}
                val parsed=runCatching {LocalDate.parse(day)}.getOrNull()
                if(parsed==null) Text("Informe uma data válida.",color=MaterialTheme.colorScheme.error)
                else {
                    val selected=language.takeUnless {it=="Todos"}
                    val total=languageTotals(sessions,parsed,selected)
                    Panel("Sua prática no dia") {
                        Text("${total.minutes} min de estudo",style=MaterialTheme.typography.headlineMedium,color=MaterialTheme.colorScheme.primary)
                        Text("${total.reviewMinutes} min de revisão no Anki · ${total.sessions} sessões")
                        HorizontalDivider()
                        Text("${total.reviewed} cards revisados · ${total.added} adicionados")
                        Text("${total.episodes} episódios / vídeos")
                    }
                    val week=(6 downTo 0).map {parsed.minusDays(it.toLong())}
                    Bars("Últimos 7 dias",week.map {"%02d/%02d".format(it.dayOfMonth,it.monthValue) to languageTotals(sessions,it,selected).minutes.toDouble()},"min")
                    Text("Tempo informado por você; não é uma avaliação de fluência.",style=MaterialTheme.typography.bodySmall)
                    Button({section="Registrar"},Modifier.fillMaxWidth()) {Text("Registrar prática")}
                }
            }
            "Registrar" -> key(generation) { LanguageEditor(null,busy,vm) {generation++;section="Progresso"} }
            else -> {
                val old=sessions.firstOrNull {it.id==editing}
                if(old!=null) {
                    TextButton({editing=null}) {Text("Voltar às sessões")}
                    key(old.id) {LanguageEditor(old,busy,vm) {editing=null}}
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

@Composable fun LanguageEditor(old: TrainingRecord?, busy: Boolean, vm: TrainingViewModel, done: ()->Unit) {
    var language by rememberSaveable {mutableStateOf(old?.extra("idioma") ?: "Inglês")}
    var custom by rememberSaveable {mutableStateOf(old?.extra("idioma")?.takeUnless {it in languageNames}.orEmpty())}
    var activity by rememberSaveable {mutableStateOf(old?.extra("atividade_idioma") ?: languageActivities[0])}
    var day by rememberSaveable {mutableStateOf(old?.data ?: today().toString())}
    var at by rememberSaveable {mutableStateOf(old?.horario?.take(5) ?: LocalTime.now(ZoneOffset.ofHours(-3)).toString().take(5))}
    var minutes by rememberSaveable {mutableStateOf(old?.durationMinutes?.toString() ?: "20")}
    var title by rememberSaveable {mutableStateOf(old?.extra("titulo").orEmpty())}
    var reviewed by rememberSaveable {mutableStateOf(old?.number("cards_revisados")?.toInt()?.toString() ?: "0")}
    var added by rememberSaveable {mutableStateOf(old?.number("cards_adicionados")?.toInt()?.toString() ?: "0")}
    var episodes by rememberSaveable {mutableStateOf((old?.number("episodios")?.toInt() ?: 1).coerceAtLeast(1).toString())}
    var audio by rememberSaveable {mutableStateOf(old?.extra("idioma_audio")?.ifBlank {language} ?: language)}
    var subtitles by rememberSaveable {mutableStateOf(old?.extra("legendas")?.takeIf {it in subtitleModes} ?: subtitleModes[0])}
    var notes by rememberSaveable {mutableStateOf(old?.extra("observacoes").orEmpty())}
    var error by remember {mutableStateOf<String?>(null)}
    Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
        Choice("Idioma que estou aprendendo",language.takeIf {it in languageNames} ?: "Outro idioma",languageNames+"Outro idioma") {language=it;audio=it.takeUnless {it=="Outro idioma"} ?: custom}
        if(language !in languageNames) Field("Nome do idioma",custom){custom=it}
        Choice("Atividade",activity,languageActivities){activity=it}
        Field("Data da sessão (AAAA-MM-DD)",day){day=it}
        Field("Horário da sessão (HH:MM)",at){at=it}
        Field("Tempo efetivo da sessão (min)",minutes,true){minutes=it}
        Field(if(activity==languageActivities[2]) "Nome da série / vídeo" else "Material ou baralho (opcional)",title){title=it}
        if(activity==languageActivities[0]) Field("Cards revisados",reviewed,true){reviewed=it}
        if(activity in languageActivities.take(2)) {
            Field("Cards adicionados ao Anki",added,true){added=it}
            Text("Registro manual. O Solem não acessa sua conta do Anki.",style=MaterialTheme.typography.bodySmall)
        }
        if(activity==languageActivities[2]) {
            Field("Episódios / vídeos vistos",episodes,true){episodes=it}
            Text("Informe o tempo total assistido acima: 2 episódios de 25 min = 50 min. Não multiplicaremos novamente.",style=MaterialTheme.typography.bodySmall)
            Field("Idioma do áudio",audio){audio=it}
            Choice("Legendas",subtitles,subtitleModes){subtitles=it}
        }
        OutlinedTextField(notes,{notes=it},Modifier.fillMaxWidth(),label={Text("Observações (opcional)")})
        error?.let {Text(it,color=MaterialTheme.colorScheme.error)}
        Button({
            val value=runCatching { languageMutation(day,at,if(language in languageNames) language else custom,activity,minutes.toIntOrNull() ?: -1,
                title,if(activity==languageActivities[0]) reviewed.toIntOrNull() ?: -1 else 0,
                if(activity in languageActivities.take(2)) added.toIntOrNull() ?: -1 else 0,
                if(activity==languageActivities[2]) episodes.toIntOrNull() ?: -1 else 0,audio,subtitles,notes,old) }
            value.onSuccess {error=null;vm.save(old?.id,it,done)}.onFailure {error=it.message ?: "Confira os dados."}
        },enabled=!busy,modifier=Modifier.fillMaxWidth()) {Text(if(busy) "Salvando…" else if(old==null) "Salvar sessão de idioma" else "Salvar alterações")}
    }
}
