package com.matheussantos.solem.domain

import java.text.Normalizer
import java.util.Locale

/** Local parsing only. A draft never calls a repository or saves a record. */
data class VoiceDraft(
    val preview: String, val items: List<MealFood> = emptyList(), val readings: List<Double> = emptyList(),
    val cumulative: Boolean = true, val mealType: String? = null, val kg: Double? = null,
    val bed: String = "", val wake: String = "", val mode: String = "auto",
    val exercise: String = "", val values: Map<String, Double> = emptyMap()
)

private fun plainVoice(text: String) = Normalizer.normalize(text.lowercase(Locale.ROOT), Normalizer.Form.NFD).replace(Regex("\\p{M}"), "")
private val numberWords = "zero um uma dois duas tres quatro cinco seis sete oito nove dez onze doze treze quatorze catorze quinze dezesseis dezassete dezessete dezoito dezenove vinte trinta quarenta cinquenta sessenta setenta oitenta noventa cem cento duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos".split(" ")
    .zip(listOf(0,1,1,2,2,3,4,5,6,7,8,9,10,11,12,13,14,14,15,16,17,17,18,19,20,30,40,50,60,70,80,90,100,100,200,300,400,500,600,700,800,900)).toMap()
fun normalizeVoice(raw: String): String {
    val words = numberWords.keys.joinToString("|")
    var text = plainVoice(raw).trim()
    text = Regex("\\b(?:$words)(?:\\s+e\\s+(?:$words))*\\b").replace(text) { m -> m.value.split(" ").filter { it != "e" }.sumOf { numberWords.getValue(it) }.toString() }
    text = Regex("(\\d+)\\s+(?:virgula|ponto)\\s+(\\d+)").replace(text, "$1.$2")
    return Regex("(\\d),(\\d)").replace(text, "$1.$2")
}
private fun leftover(text: String) = text.replace(Regex("[\\s,;:.!]+"), " ").trim()
private fun voiceNumber(text: String, min: Double = 0.0, max: Double = 34000.0): Double = text.toDouble().also {
    require(it.isFinite() && it in min..max) { "Valor fora do intervalo permitido. Confira a transcrição." }
}
private fun amountVoice(value: Double) = if (value % 1.0 == 0.0) value.toLong().toString() else value.toString().replace('.', ',')

fun parseMealVoice(raw: String, foods: List<MealReference>, defaultCumulative: Boolean = true): VoiceDraft {
    var text = normalizeVoice(raw)
    val accumulated = Regex("\\bacumulad[oa]s?\\b").containsMatchIn(text)
    val individual = Regex("\\bindividu(?:al|ais)\\b").containsMatchIn(text)
    require(!(accumulated && individual)) { "Diga apenas um modo: acumulado ou individual." }
    val cumulative = if(accumulated || individual) accumulated else defaultCumulative
    text = text.replace(Regex("\\b(?:peso[s]?\\s+)?(?:acumulad[oa]s?|individu(?:al|ais))(?:\\s+da\\s+balanca)?\\b"), " ")
    var mealType: String? = null
    linkedMapOf("cafe da manha" to "Café da manhã", "lanche da tarde" to "Lanche da tarde", "almoco" to "Almoço", "jantar" to "Jantar", "outra refeicao" to "Outra").forEach { (spoken,label) ->
        val pattern = Regex("\\b$spoken\\b")
        if(pattern.containsMatchIn(text)) {
            require(mealType == null) { "Diga apenas uma refeição por vez." }
            mealType = label; text = text.replace(pattern, " ")
        }
    }
    val aliases = foods.associateBy { plainVoice(it.displayName) }.toMutableMap()
    mapOf("ovo" to "Ovo cozido", "pure" to "Purê de batata", "salada de alface" to "Alface", "bolacha recheada" to "Biscoito recheado").forEach { (alias,target) -> foods.firstOrNull { it.displayName == target }?.let { aliases[alias] = it } }
    val names = aliases.keys.sortedByDescending { it.length }.joinToString("|") { Regex.escape(it) }
    val pattern = Regex("\\b($names)\\s*(?:[:=]|com)?\\s*(\\d+(?:\\.\\d+)?)\\s*(?:gramas?\\b|g\\b)?")
    val matches = pattern.findAll(text).toList()
    val rest = text.replace(pattern, " ").replace(Regex("\\b(?:e|de|no|na|o|a|coloquei|colocar|refeicao|registrar|registra|balanca|pesos|peso)\\b"), " ")
    require(leftover(rest).isEmpty() && matches.size in 1..12) { "Não entendi a lista completa. Diga alimento e leitura em gramas: arroz 170, feijão 323, acumulado. Confira alimentos e números." }
    val readings = matches.map { voiceNumber(it.groupValues[2], 0.1) }
    var before = 0.0
    val items = matches.mapIndexed { i, match ->
        val grams = if(cumulative) readings[i] - before else readings[i]
        require(grams > 0 && grams <= 2000) { "As leituras acumuladas devem aumentar, com até 2000 g adicionados por alimento. Confira o modo e a ordem." }
        before = readings[i]
        val food = aliases.getValue(match.groupValues[1])
        MealFood(name=food.name, foodId=food.id, grams=kotlin.math.round(grams*1000)/1000)
    }
    val preview = (if(cumulative) "Peso acumulado da balança · prato tarado (0 g)" else "Peso individual de cada alimento") +
        "\n" + (mealType ?: "Tipo de refeição atual") + "\n" + items.mapIndexed { i, item ->
            val name = foods.first { it.id == item.foodId }.displayName
            "$name: ${amountVoice(readings[i])} g → porção ${amountVoice(item.grams)} g"
        }.joinToString("\n") + "\nConfira também as referências de preparo. Esta lista substitui o rascunho atual."
    return VoiceDraft(preview,items,readings,cumulative,mealType)
}

fun parseWeightVoice(raw: String): VoiceDraft {
    val match = Regex("(?:meu peso(?: e)?|peso|estou com|pesei)?\\s*(\\d+(?:\\.\\d+)?)\\s*(?:kg|quilos?|quilogramas?)?[.!]?").matchEntire(normalizeVoice(raw))
    requireNotNull(match) { "Diga apenas o peso em kg: peso 67 vírgula 5 quilos." }
    val value = voiceNumber(match.groupValues[1],1.0,500.0)
    return VoiceDraft("Peso: ${amountVoice(value)} kg",kg=value)
}

fun parseSleepVoice(raw: String): VoiceDraft {
    var text = plainVoice(raw); var mode = "auto"
    val hours=(listOf("vinte e tres","vinte e duas","vinte e dois","vinte e uma","vinte e um")+numberWords.filterValues {it<24}.keys).joinToString("|")+"|\\d{1,2}"
    val words=numberWords.keys.joinToString("|")
    val minutes="(?:$words)(?:\\s+e\\s+(?:$words))*|\\d{1,2}|meia"
    text=Regex("\\b(dormi|acordei)(?: as)?\\s+($hours)(?: horas?)? e ($minutes)\\b").replace(text){m->
        m.groupValues[1]+" as "+normalizeVoice(m.groupValues[2])+":"+if(m.groupValues[3]=="meia")"30" else normalizeVoice(m.groupValues[3])
    }
    text=normalizeVoice(text)
    mapOf("na mesma data" to "same", "na noite anterior" to "previous").forEach { (phrase,value) ->
        if(text.contains(phrase)) {mode=value; text=text.replace(phrase, "")}
    }
    text=text.trim(' ', ',', '.', '!')
    val time = "(\\d{1,2})(?:(?::|h| horas? e | e )(\\d{1,2}|meia))?(?:\\s*horas?)?"
    val match = Regex("\\s*dormi(?: as)?\\s+$time\\s*(?:e|,)\\s*acordei(?: as)?\\s+$time\\s*[.!]?\\s*").matchEntire(text)
    requireNotNull(match) { "Use 24 horas: dormi às 3 e acordei às 13:30. Pode dizer na mesma data ou na noite anterior." }
    fun clock(h: String, m: String): String {
        val hour=h.toInt(); val minute=if(m=="meia")30 else m.toIntOrNull() ?: 0
        require(hour in 0..23 && minute in 0..59) { "Confira os horários: horas de 0 a 23 e minutos de 0 a 59." }
        return "%02d:%02d".format(Locale.ROOT,hour,minute)
    }
    val bed=clock(match.groupValues[1],match.groupValues[2]); val wake=clock(match.groupValues[3],match.groupValues[4])
    val label=when(mode){"same"->"mesma data";"previous"->"noite anterior";else->"datas automáticas"}
    return VoiceDraft("Dormiu $bed · acordou $wake · $label",bed=bed,wake=wake,mode=mode)
}

fun parseWorkoutVoice(raw: String, exercises: List<String>, current: String): VoiceDraft {
    var text=normalizeVoice(raw)
    val aliases=exercises.associateBy {plainVoice(it)}.mapValues {it.value}.toMutableMap()
    mapOf("flexoes" to "Flexão","agachamentos" to "Agachamento","barras pronadas" to "Barra Fixa (Pronada)","barras supinadas" to "Barra Fixa (Supinada)").forEach {(alias,name)->if(name in exercises)aliases[alias]=name}
    val found=mutableListOf<String>()
    aliases.keys.sortedByDescending {it.length}.forEach {alias->
        val pattern=Regex("(?<!\\w)${Regex.escape(alias)}(?!\\w)")
        if(pattern.containsMatchIn(text)){found+=aliases.getValue(alias);text=text.replace(pattern," ")}
    }
    require(found.distinct().size<=1){"Registre um exercício por vez."}
    val exercise=found.firstOrNull() ?: current
    val values=mutableMapOf<String,Double>()
    val series=Regex("\\b(\\d+) series de (\\d+)(?: repeticoes)?")
    series.find(text)?.let {m-> values["series"]=m.groupValues[1].toDouble();values["repeticoes"]=m.groupValues[1].toDouble()*m.groupValues[2].toDouble();text=text.replaceRange(m.range," ")}
    val patterns=listOf(
        "descanso_seg" to "(?:descanso(?: de)?\\s+)(\\d+)\\s*(segundos?|minutos?)",
        "series" to "(\\d+)\\s*series?", "repeticoes" to "(\\d+)\\s*(?:repeticoes|reps?|tentativas?)",
        "carga_kg" to "(?:carga(?: de)?\\s+)(\\d+(?:\\.\\d+)?)\\s*(?:kg|quilos?)",
        "distancia_km" to "(\\d+(?:\\.\\d+)?)\\s*(?:km|quilometros?)", "duracao_min" to "(\\d+)\\s*minutos?", "isometria_segundos" to "(\\d+)\\s*segundos?")
    patterns.forEach {(field,source)->
        val pattern=Regex(source);val matches=pattern.findAll(text).toList()
        require(matches.size<=1 && !(matches.isNotEmpty() && field in values)){"Há dois valores para o mesmo campo. Confira a transcrição."}
        matches.firstOrNull()?.let {m->
            var value=voiceNumber(m.groupValues[1],0.0,86400.0)
            if(field=="descanso_seg" && m.groupValues[2].startsWith("minuto"))value*=60
            values[field]=value;text=text.replace(pattern," ")
        }
    }
    if(found.isNotEmpty() && Regex("\\s*(?:fiz\\s+)?\\d+\\s*[.!]?\\s*").matches(text) && "repeticoes" !in values){values["repeticoes"]=Regex("\\d+").find(text)!!.value.toDouble();text=""}
    text=text.replace(Regex("\\b(?:fiz|de|e|duracao|total|tempo|sustentado)\\b")," ")
    require(leftover(text).isEmpty() && values.isNotEmpty()){ "Confira a frase: agachamento, 3 séries de 20, descanso de 60 segundos. Para caminhada: 30 minutos, 2 quilômetros." }
    require(values.values.all {it.isFinite() && it in 0.0..86400.0}) {"Valores muito altos. Confira as quantidades e unidades."}
    val labels=mapOf("series" to "Séries","repeticoes" to "Repetições totais","carga_kg" to "Carga (kg)","descanso_seg" to "Descanso (s)","duracao_min" to "Duração (min)","distancia_km" to "Distância (km)","isometria_segundos" to "Tempo sustentado (s)")
    return VoiceDraft(exercise+"\n"+values.map {(k,v)->"${labels[k]}: ${amountVoice(v)}"}.joinToString("\n"),exercise=exercise,values=values)
}
