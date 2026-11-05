"""Solem's deterministic spaced review, shared with Android; times are UTC epoch seconds.

Four self-ratings, short learning steps then growing daily intervals. This is not
Anki's FSRS and does not read or change the user's Anki collection.
"""
import math

RATINGS = ("Errei", "Difícil", "Bom", "Fácil")


def review_state(value=None):
    value = value if isinstance(value, dict) else {}
    def integer(key, default, low, high):
        n = value.get(key, default)
        return max(low, min(high, n)) if type(n) is int else default
    return dict(schema=1, due_at=integer('due_at', 0, 0, 32503680000),
                interval_days=integer('interval_days', 0, 0, 36500),
                ease_milli=integer('ease_milli', 2500, 1300, 3000),
                step=integer('step', 0, 0, 1), reviews=integer('reviews', 0, 0, 1000000),
                lapses=integer('lapses', 0, 0, 1000000),
                last_review_at=integer('last_review_at', 0, 0, 32503680000))


def schedule_review(value, rating, now):
    if rating not in RATINGS: raise ValueError('Escolha como foi lembrar da resposta.')
    result = review_state(value)
    if result['due_at'] > now: raise ValueError('Este cartão já foi revisado. Atualize a fila.')
    days, ease = result['interval_days'], result['ease_milli']
    if rating == 'Errei':
        seconds = 60
        result.update(interval_days=0, step=0,
                      lapses=result['lapses'] + (1 if days else 0),
                      ease_milli=max(1300, ease-200) if days else ease)
    elif not days:
        if rating == 'Difícil': seconds = 300 if result['step']==0 else 600
        elif rating == 'Bom' and result['step']==0:
            seconds=600; result['step']=1
        else:
            result['interval_days']=4 if rating=='Fácil' else 1
            seconds=result['interval_days']*86400
    else:
        factor = 1.2 if rating=='Difícil' else ease/1000 * (1.3 if rating=='Fácil' else 1)
        interval = min(36500, max(days+1, math.floor(days*factor+0.5)))
        result.update(interval_days=interval,
                      ease_milli=max(1300,min(3000,ease+(-150 if rating=='Difícil' else 150 if rating=='Fácil' else 0))))
        seconds=interval*86400
    result.update(due_at=int(now)+seconds, last_review_at=int(now), reviews=result['reviews']+1)
    return result


def interval_label(seconds):
    return f'{seconds//86400} d' if seconds>=86400 else f'{max(1,seconds//60)} min'
