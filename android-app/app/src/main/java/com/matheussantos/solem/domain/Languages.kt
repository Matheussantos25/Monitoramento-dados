package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.*
import kotlinx.serialization.json.*
import java.time.LocalDate
import java.time.LocalTime
import java.util.Locale

val languageNames = listOf("Inglês", "Espanhol", "Francês", "Italiano", "Alemão", "Japonês", "Coreano", "Mandarim")
val languageActivities = listOf("Revisão no Anki", "Criação de cards", "Série / vídeo", "Leitura", "Conversação", "Escuta", "Escrita", "Aula / prática")
val contentTypes = listOf("Série", "Anime", "Filme", "Vídeo", "Podcast", "Música", "Audiolivro", "Outro")
val languageSources = listOf("YouTube", "Netflix", "Prime Video", "Disney+", "Crunchyroll", "Spotify", "Arquivo / offline", "Outro")
fun languageMediaActivity(activity:String) = activity in listOf(languageActivities[2], "Escuta")
fun languageMaterialLabel(activity:String) = when(activity) {
    languageActivities[0],languageActivities[1] -> "Baralho do Anki (opcional)"
    "Leitura" -> "Livro, artigo ou texto (opcional)"
    "Conversação" -> "Tema da conversa (opcional)"
    "Escrita" -> "Tema ou texto produzido (opcional)"
    else -> "Curso ou assunto (opcional)"
}
val subtitleModes = listOf("No idioma estudado", "Em português", "Sem legenda", "Outro idioma")

/** Defaults for the next entry, never a copy of session counts, notes or timestamps. */
data class LanguageEntryContext(
    val activity:String=languageActivities[0], val language:String="Inglês",
    val title:String="", val source:String="", val contentType:String=contentTypes[0],
    val audio:String="Inglês", val subtitles:String=subtitleModes[0]
) : java.io.Serializable

fun TrainingMutation.languageEntryContext():LanguageEntryContext {
    fun text(key:String)=extras[key]?.jsonPrimitive?.contentOrNull.orEmpty()
    return LanguageEntryContext(text("atividade_idioma"),text("idioma"),text("titulo"),
        text("fonte_idioma"),text("tipo_conteudo").ifBlank {contentTypes[0]},
        text("idioma_audio").ifBlank {text("idioma")},
        text("legendas").takeIf {it in subtitleModes} ?: subtitleModes[0])
}
val languagePeriods = listOf("Dia", "Últimos 7 dias", "Mês", "Semestre", "Ano")
val sessionTimes = (0 until 1440).map {"%02d:%02d".format(Locale.ROOT,it/60,it%60)}
fun sessionTime(value:String):String {
    val text=value.trim()
    val result=when {
        text.matches(Regex("\\d{1,2}"))->text.padStart(2,'0')+":00"
        text.matches(Regex("\\d{3,4}"))->text.padStart(4,'0').let {it.take(2)+":"+it.takeLast(2)}
        text.matches(Regex("\\d{1,2}:\\d{2}(:\\d{2})?"))->text.padStart(if(text.count {it==':'}==2)8 else 5,'0')
        else->throw IllegalArgumentException("Informe um horário válido: 22, 2215 ou 22:15.")
    }
    require(runCatching {LocalTime.parse(result)}.isSuccess) {"Use um horário entre 00:00 e 23:59."}
    return result
}
fun timeSuggestions(query:String)=sessionTimes.filter {it.replace(":","").startsWith(query.trim().replace(":",""))}
fun languageMediaTitles(records:List<TrainingRecord>):List<String> = records
    .filter {it.isLanguage() && languageMediaActivity(it.extra("atividade_idioma")) && it.extra("titulo").isNotBlank()}
    .sortedWith(compareByDescending<TrainingRecord> {it.data}.thenByDescending {it.horario})
    .map {it.extra("titulo").trim()}.distinctBy {it.lowercase(Locale.ROOT)}
fun languagePeriodBounds(day:LocalDate,period:String):Pair<LocalDate,LocalDate> = when(period) {
    "Dia"->day to day
    "Últimos 7 dias"->day.minusDays(6) to day
    "Mês"->day.withDayOfMonth(1) to day.withDayOfMonth(day.lengthOfMonth())
    "Semestre"->LocalDate.of(day.year,if(day.monthValue<=6)1 else 7,1).let {it to it.plusMonths(6).minusDays(1)}
    "Ano"->LocalDate.of(day.year,1,1) to LocalDate.of(day.year,12,31)
    else->throw IllegalArgumentException("Escolha um período válido.")
}
fun languageRangeRecords(records:List<TrainingRecord>,start:LocalDate,end:LocalDate,language:String?=null)=records.filter {
    val day=runCatching {LocalDate.parse(it.data.take(10))}.getOrNull()
    it.isLanguage() && day!=null && day>=start && day<=end && (language==null || it.extra("idioma")==language)
}.distinctBy {it.id}
fun languageRangeTotals(records:List<TrainingRecord>,start:LocalDate,end:LocalDate,language:String?=null):LanguageTotals {
    val rows=languageRangeRecords(records,start,end,language)
    return LanguageTotals(rows.sumOf {it.durationMinutes},rows.filter {it.extra("atividade_idioma")==languageActivities[0]}.sumOf {it.durationMinutes},
        rows.sumOf {it.number("cards_revisados").toInt()},rows.sumOf {it.number("cards_adicionados").toInt()},rows.sumOf {it.number("episodios").toInt()},rows.size)
}
fun languageChart(records:List<TrainingRecord>,start:LocalDate,end:LocalDate,period:String,language:String?=null):List<Pair<String,Double>> {
    fun daily(day:LocalDate)="%02d/%02d".format(Locale.ROOT,day.dayOfMonth,day.monthValue)
    fun monthly(day:LocalDate)="%02d/%04d".format(Locale.ROOT,day.monthValue,day.year)
    val keys=when(period) {
        "Dia"->(0..23).map {"%02dh".format(Locale.ROOT,it)}
        "Semestre","Ano"->(start.monthValue..end.monthValue).map {monthly(LocalDate.of(start.year,it,1))}
        else->generateSequence(start){it.plusDays(1)}.takeWhile {it<=end}.map(::daily).toList()
    }
    val totals=keys.associateWith {0.0}.toMutableMap()
    languageRangeRecords(records,start,end,language).forEach {
        val day=LocalDate.parse(it.data.take(10))
        val key=when(period){"Dia"->it.horario.take(2)+"h";"Semestre","Ano"->monthly(day);else->daily(day)}
        if(key in totals)totals[key]=totals.getValue(key)+it.durationMinutes
    }
    return keys.map {it to totals.getValue(it)}
}
fun TrainingRecord.isLanguage() = group == "Estudos" && number("language_schema") == 1.0

data class LanguageTotals(val minutes: Int, val reviewMinutes: Int, val reviewed: Int, val added: Int, val episodes: Int, val sessions: Int)
fun languageTotals(records: List<TrainingRecord>, day: LocalDate, language: String? = null): LanguageTotals {
    val rows=records.filter { it.isLanguage() && it.data.take(10)==day.toString() && (language==null || it.extra("idioma")==language) }.distinctBy { it.id }
    return LanguageTotals(rows.sumOf {it.durationMinutes}, rows.filter {it.extra("atividade_idioma")==languageActivities[0]}.sumOf {it.durationMinutes},
        rows.sumOf {it.number("cards_revisados").toInt()}, rows.sumOf {it.number("cards_adicionados").toInt()}, rows.sumOf {it.number("episodios").toInt()},rows.size)
}

fun languageMutation(day: String, at: String, language: String, activity: String, minutes: Int,
    title: String="", reviewed: Int=0, added: Int=0, episodes: Int=0, audio: String="", subtitles: String="", notes: String="", old: TrainingRecord?=null, source:String="", contentType:String=""): TrainingMutation {
    LocalDate.parse(day); LocalTime.parse(at)
    require(language.trim().length in 1..60 && activity in languageActivities) {"Informe idioma e atividade."}
    require(minutes in 1..1440) {"Informe de 1 a 1.440 minutos de prática."}
    require(title.trim().length<=160 && notes.trim().length<=2000) {"Título: até 160 caracteres. Observações: até 2.000."}
    require(listOf(reviewed,added,episodes).all {it in 0..10000}) {"Use contagens inteiras entre 0 e 10.000."}
    val media=languageMediaActivity(activity)
    require(activity!=languageActivities[2] || (title.isNotBlank() && episodes in 1..100 && audio.isNotBlank() && subtitles in subtitleModes)) {"Informe título, episódios, áudio e legendas."}
    require(source.trim().length<=100 && (contentType.isEmpty() || contentType in contentTypes)) {"Confira a fonte e o tipo de conteúdo."}
    require(!media || (episodes<=100 && (subtitles.isEmpty() || subtitles in subtitleModes))) {"Confira a quantidade e as legendas."}
    val extras=buildJsonObject {
        old?.extras?.filterKeys {it!="tempo_segundos_exato"}?.forEach { (k,v)->put(k,v) }
        put("language_schema",1);put("idioma",language.trim());put("atividade_idioma",activity);put("titulo",title.trim())
        put("cards_revisados",if(activity==languageActivities[0]) reviewed else 0)
        put("cards_adicionados",if(activity in languageActivities.take(2)) added else 0)
        put("episodios",if(media) episodes else 0);put("idioma_audio",if(media) audio.trim().take(60) else "")
        put("legendas",if(activity=="Escuta") "Sem legenda" else if(media) subtitles else "");put("observacoes",notes.trim())
        put("fonte_idioma",if(activity !in languageActivities.take(2)) source.trim() else "")
        put("tipo_conteudo",if(media) contentType else "")
        put("fonte_questoes","Idiomas");put("tempo_video",0);put("q_certas",0);put("q_erradas",0)
    }
    return TrainingMutation(day,at,"Estudos",language.trim(),durationMinutes=minutes,extras=extras)
}
