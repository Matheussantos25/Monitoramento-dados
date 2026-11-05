package com.matheussantos.solem.domain

import kotlinx.serialization.Serializable
import kotlin.math.floor

val vocabularyRatings=listOf("Errei","Difícil","Bom","Fácil")
@Serializable data class VocabularyReview(
    val schema:Int=1, val due_at:Long=0, val interval_days:Int=0, val ease_milli:Int=2500,
    val step:Int=0, val reviews:Int=0, val lapses:Int=0, val last_review_at:Long=0
)
fun VocabularyReview.normalized()=copy(schema=1,due_at=due_at.coerceIn(0,32503680000L),
    interval_days=interval_days.coerceIn(0,36500),ease_milli=ease_milli.coerceIn(1300,3000),
    step=step.coerceIn(0,1),reviews=reviews.coerceIn(0,1000000),lapses=lapses.coerceIn(0,1000000),
    last_review_at=last_review_at.coerceIn(0,32503680000L))

/** Solem review schedule, mirrored in solem_vocabulary_review.py; not Anki FSRS. */
fun scheduleVocabularyReview(state:VocabularyReview?,rating:String,now:Long):VocabularyReview {
    require(rating in vocabularyRatings) {"Escolha como foi lembrar da resposta."}
    var result=(state ?: VocabularyReview()).normalized()
    require(result.due_at<=now) {"Este cartão já foi revisado. Atualize a fila."}
    val days=result.interval_days;val ease=result.ease_milli
    val seconds:Long
    if(rating=="Errei") {
        seconds=60
        result=result.copy(interval_days=0,step=0,lapses=result.lapses+if(days>0)1 else 0,
            ease_milli=if(days>0)(ease-200).coerceAtLeast(1300) else ease)
    } else if(days==0) {
        if(rating=="Difícil")seconds=if(result.step==0)300 else 600
        else if(rating=="Bom" && result.step==0) {seconds=600;result=result.copy(step=1)}
        else {result=result.copy(interval_days=if(rating=="Fácil")4 else 1);seconds=result.interval_days*86400L}
    } else {
        val factor=if(rating=="Difícil")1.2 else ease/1000.0*(if(rating=="Fácil")1.3 else 1.0)
        val interval=maxOf(days+1,floor(days*factor+0.5).toInt()).coerceAtMost(36500)
        result=result.copy(interval_days=interval,ease_milli=(ease+when(rating){"Difícil"->-150;"Fácil"->150;else->0}).coerceIn(1300,3000))
        seconds=interval*86400L
    }
    return result.copy(due_at=now+seconds,last_review_at=now,reviews=result.reviews+1)
}
fun vocabularyInterval(seconds:Long)=if(seconds>=86400)"${seconds/86400} d" else "${maxOf(1,seconds/60)} min"
