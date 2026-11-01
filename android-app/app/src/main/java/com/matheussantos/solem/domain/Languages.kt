package com.matheussantos.solem.domain

import com.matheussantos.solem.data.model.*
import kotlinx.serialization.json.*
import java.time.LocalDate
import java.time.LocalTime

val languageNames = listOf("Inglês", "Espanhol", "Francês", "Italiano", "Alemão", "Japonês", "Coreano", "Mandarim")
val languageActivities = listOf("Revisão no Anki", "Criação de cards", "Série / vídeo", "Leitura", "Conversação", "Escuta", "Escrita", "Aula / prática")
val subtitleModes = listOf("No idioma estudado", "Em português", "Sem legenda", "Outro idioma")
fun TrainingRecord.isLanguage() = group == "Estudos" && number("language_schema") == 1.0

data class LanguageTotals(val minutes: Int, val reviewMinutes: Int, val reviewed: Int, val added: Int, val episodes: Int, val sessions: Int)
fun languageTotals(records: List<TrainingRecord>, day: LocalDate, language: String? = null): LanguageTotals {
    val rows=records.filter { it.isLanguage() && it.data.take(10)==day.toString() && (language==null || it.extra("idioma")==language) }.distinctBy { it.id }
    return LanguageTotals(rows.sumOf {it.durationMinutes}, rows.filter {it.extra("atividade_idioma")==languageActivities[0]}.sumOf {it.durationMinutes},
        rows.sumOf {it.number("cards_revisados").toInt()}, rows.sumOf {it.number("cards_adicionados").toInt()}, rows.sumOf {it.number("episodios").toInt()},rows.size)
}

fun languageMutation(day: String, at: String, language: String, activity: String, minutes: Int,
    title: String="", reviewed: Int=0, added: Int=0, episodes: Int=0, audio: String="", subtitles: String="", notes: String="", old: TrainingRecord?=null): TrainingMutation {
    LocalDate.parse(day); LocalTime.parse(at)
    require(language.trim().length in 1..60 && activity in languageActivities) {"Informe idioma e atividade."}
    require(minutes in 1..1440) {"Informe de 1 a 1.440 minutos de prática."}
    require(title.trim().length<=160 && notes.trim().length<=2000) {"Título: até 160 caracteres. Observações: até 2.000."}
    require(listOf(reviewed,added,episodes).all {it in 0..10000}) {"Use contagens inteiras entre 0 e 10.000."}
    val media=activity==languageActivities[2]
    require(!media || (title.isNotBlank() && episodes in 1..100 && audio.isNotBlank() && subtitles in subtitleModes)) {"Informe título, episódios, áudio e legendas."}
    val extras=buildJsonObject {
        old?.extras?.filterKeys {it!="tempo_segundos_exato"}?.forEach { (k,v)->put(k,v) }
        put("language_schema",1);put("idioma",language.trim());put("atividade_idioma",activity);put("titulo",title.trim())
        put("cards_revisados",if(activity==languageActivities[0]) reviewed else 0)
        put("cards_adicionados",if(activity in languageActivities.take(2)) added else 0)
        put("episodios",if(media) episodes else 0);put("idioma_audio",if(media) audio.trim().take(60) else "")
        put("legendas",if(media) subtitles else "");put("observacoes",notes.trim())
        put("fonte_questoes","Idiomas");put("tempo_video",0);put("q_certas",0);put("q_erradas",0)
    }
    return TrainingMutation(day,at,"Estudos",language.trim(),durationMinutes=minutes,extras=extras)
}
