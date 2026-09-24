"""Health and workout summaries derived from the existing treinos records.

Meal detail, water and sleep are stored in dados_extras so old rows remain valid.
No health quantity generates XP; the existing progress rules remain unchanged.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from solem_progress import extras_of, number, record_date

MEAL_TYPES = ("Café da manhã", "Lanche da manhã", "Almoço", "Lanche da tarde", "Jantar", "Ceia", "Outra")
CALISTHENICS = ("Peitoral", "Costas", "Pernas", "Abdominal")
EXERCISE_GROUPS = {
    "Peitoral": "empurrar", "Costas": "puxar", "Bíceps": "puxar",
    "Pernas": "pernas", "Abdominal": "core", "Skills / Calistenia": "habilidade",
}

# Single source for the web form and the Android catalog. These are existing
# columns in treinos (isometria_segundos lives in dados_extras).
WORKOUT_FIELD_PROFILES = {
    "cardio": ("duracao_min", "distancia_km"),
    "counted_cardio": ("repeticoes", "duracao_min"),
    "isometric": ("repeticoes", "isometria_segundos"),
    "timed": ("duracao_min",),
    "counted": ("repeticoes",),
    "bodyweight": ("series", "repeticoes", "descanso_seg"),
    "resistance": ("series", "repeticoes", "carga_kg", "descanso_seg"),
}
WORKOUT_EXERCISE_PROFILES = {
    "Caminhada": "cardio", "Corrida": "cardio", "Bike": "cardio",
    "Pular Corda": "counted_cardio", "Pular Normal": "counted_cardio",
    "Subida Escada (Andares)": "counted_cardio",
    "Prancha": "isometric", "L-Sit": "isometric",
    "Handstand (Parada de Mãos)": "isometric",
    "Massagem Facial": "timed", "Mewing com borracha": "counted",
    "Abdominal Levantada": "bodyweight", "Barra Fixa (Supinada)": "bodyweight",
    "Barra Fixa (Pronada)": "bodyweight", "Flexão": "bodyweight",
    "Agachamento": "bodyweight",
    "Puxada Alta": "resistance", "Remada Baixa": "resistance",
    "Remada em Pé na Polia": "resistance",
    "Remada em Pé na Polia com barra": "resistance",
}


def workout_fields(exercise):
    profile = WORKOUT_EXERCISE_PROFILES.get(exercise, "resistance")
    return WORKOUT_FIELD_PROFILES[profile]


def format_one_decimal(value):
    return f"{value:.1f}".rstrip("0").rstrip(".")


def now_local():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


def base_record(day, time, group, exercise, *, extras=None, **values):
    record = dict(data=str(day), horario=str(time), grupo_muscular=group, exercicio=exercise,
                  series=0, repeticoes=0, carga_kg=0.0, descanso_seg=0, duracao_min=0,
                  distancia_km=0.0, alimentacao_saudavel="", alimentacao_besteirol="",
                  peso_corporal=0.0, dados_extras=extras or {})
    record.update(values)
    return record


def records_on(records, day, group=None, exercise=None):
    return [row for row in records if record_date(row.get("data")) == day
            and (group is None or row.get("grupo_muscular") == group)
            and (exercise is None or row.get("exercicio") == exercise)]


def daily_water_ml(records, day):
    total = 0
    for row in records_on(records, day, "Nutrição", "Água"):
        extra = extras_of(row.get("dados_extras"))
        size, count = number(extra.get("volume_ml")), number(extra.get("quantidade"))
        if 0 < size <= 5000 and 0 < count <= 50:
            total += round(size * count)
    return total


def sleep_minutes(bedtime, wake):
    start = datetime.strptime(bedtime, "%H:%M")
    end = datetime.strptime(wake, "%H:%M")
    minutes = int((end - start).total_seconds() / 60) % (24 * 60)
    if not 1 <= minutes <= 16 * 60:
        raise ValueError("Informe horários que correspondam a um período de até 16 horas.")
    return minutes


def training_stats(records, exercise):
    rows = [row for row in records if row.get("exercicio") == exercise and
            row.get("grupo_muscular") not in ("Nutrição", "Métricas", "Estudos") and
            record_date(row.get("data")) is not None]
    rows.sort(key=lambda row: (record_date(row.get("data")), str(row.get("horario", ""))))
    if not rows:
        return None
    totals = {}
    for row in rows:
        day = record_date(row.get("data"))
        totals[day] = totals.get(day, 0) + number(row.get("repeticoes"))
    last = rows[-1]
    best = max(rows, key=lambda row: number(row.get("repeticoes")))
    return dict(last=last, best=best, days=len(totals),
                average_reps_per_day=sum(totals.values()) / len(totals),
                last_day=record_date(last.get("data")))


def training_measure_stats(records, exercise):
    """Use the unit actually recorded for an exercise, not reps for cardio."""
    rows = [row for row in records if row.get("exercicio") == exercise and
            row.get("grupo_muscular") not in ("Nutrição", "Métricas", "Estudos") and
            record_date(row.get("data")) is not None]
    if not rows:
        return None
    profile = WORKOUT_EXERCISE_PROFILES.get(exercise)
    if profile == "cardio":
        candidates = (("distancia_km", "km"), ("duracao_min", "min"))
    elif profile == "isometric":
        candidates = (("isometria_segundos", "seg"), ("repeticoes", "rep"))
    elif profile == "timed":
        candidates = (("duracao_min", "min"),)
    else:
        candidates = (("repeticoes", "rep"), ("duracao_min", "min"),
                      ("isometria_segundos", "seg"), ("distancia_km", "km"))
    def measured(row, field):
        return number(extras_of(row.get("dados_extras")).get(field)) if field == "isometria_segundos" else number(row.get(field))
    field, unit = next(((field, unit) for field, unit in candidates
                        if any(measured(row, field) > 0 for row in rows)), candidates[0])
    rows.sort(key=lambda row: (record_date(row.get("data")), str(row.get("horario", ""))))
    days = {}
    for row in rows:
        day = record_date(row.get("data"))
        days[day] = days.get(day, 0.0) + measured(row, field)
    return {"unit": unit, "last": measured(rows[-1], field),
            "record": max(measured(row, field) for row in rows),
            "average_per_day": sum(days.values()) / len(days),
            "days": len(days), "last_day": record_date(rows[-1].get("data"))}


def private_weight_history(entries):
    """Chronological weight points from the owner-scoped health diary only."""
    points = []
    for row in entries:
        if row.get("kind") != "weight":
            continue
        day = record_date(row.get("day"))
        kg = number((row.get("details") or {}).get("kg"))
        if day is not None and 1 <= kg <= 500:
            points.append((day, kg))
    return sorted(points)


def training_category_stats(records, group):
    days = {}
    for row in records:
        day = record_date(row.get("data"))
        if row.get("grupo_muscular") == group and day is not None:
            days[day] = days.get(day, 0) + number(row.get("repeticoes"))
    if not days:
        return None
    return {"days": len(days), "average_reps_per_day": sum(days.values()) / len(days)}


def training_recommendation(records, today=None):
    """Suggest the least recently used calisthenics group, not a prescription."""
    today = today or now_local().date()
    latest = {group: None for group in CALISTHENICS}
    for row in records:
        group = row.get("grupo_muscular")
        day = record_date(row.get("data"))
        if group in latest and day is not None and day <= today:
            if latest[group] is None or day > latest[group]:
                latest[group] = day
    group = min(CALISTHENICS, key=lambda key: (latest[key] or date.min, CALISTHENICS.index(key)))
    elapsed = (today - latest[group]).days if latest[group] else None
    if elapsed is not None and elapsed < 2:
        return dict(group=None, message="Os grupos principais aparecem treinados recentemente. Considere um dia leve ou de recuperação.")
    label = {"Peitoral":"empurrar", "Costas":"puxar", "Pernas":"pernas", "Abdominal":"core"}[group]
    when = "ainda não há registro" if elapsed is None else f"último registro há {elapsed} dia(s)"
    return dict(group=group, message=f"Sugestão de hoje: {label} · {when}. Ajuste ao seu descanso e à sua disposição.")
