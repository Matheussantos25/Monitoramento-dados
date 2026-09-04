"""Progress derived from existing records; no new database tables or counters."""
from datetime import date, datetime, timedelta
import json
import math


def number(value):
    try:
        result = float(value)
        return max(0, result) if math.isfinite(result) else 0
    except (TypeError, ValueError):
        return 0


def extras_of(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            pass
    return {}


def record_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


def category_of(row):
    group = row.get("grupo_muscular")
    extra = extras_of(row.get("dados_extras"))
    if group == "Estudos":
        values = [row.get("duracao_min"), row.get("repeticoes"), extra.get("tempo_video"),
                  extra.get("q_certas"), extra.get("q_erradas"), extra.get("tempo_segundos_exato")]
        return "estudo" if any(number(v) > 0 for v in values) else None
    if group == "Nutrição":
        values = [row.get("alimentacao_saudavel"), row.get("alimentacao_besteirol")]
        return "alimentação" if any(isinstance(v, str) and v.strip() for v in values) else None
    if group == "Métricas" or not group:
        return None
    values = [row.get("repeticoes"), row.get("duracao_min"), row.get("distancia_km"),
              extra.get("isometria_segundos")]
    return "treino" if any(number(v) > 0 for v in values) else None


def calculate_progress(records, today=None):
    today = today or (datetime.utcnow() - timedelta(hours=3)).date()
    days = {}
    valid = []
    for row in records:
        day = record_date(row.get("data"))
        if day is None or day > today:
            continue
        category = category_of(row)
        if category:
            days.setdefault(day, set()).add(category)
            valid.append((day, category, row))

    def daily_xp(categories):
        return sum({"treino": 30, "estudo": 30, "alimentação": 10}[c] for c in categories) + (
            15 if {"treino", "estudo"} <= categories else 0)

    xp = sum(daily_xp(categories) for categories in days.values())
    streak = 0
    cursor = today if today in days else today - timedelta(days=1)
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)

    week_start = today - timedelta(days=today.weekday())
    week = [week_start + timedelta(days=i) for i in range(7)]
    week_workouts = len({day for day, category, _ in valid if category == "treino" and day >= week_start})
    study_minutes = 0
    questions = 0
    for day, category, row in valid:
        if category != "estudo" or day < week_start:
            continue
        extra = extras_of(row.get("dados_extras"))
        exact = extra.get("tempo_segundos_exato")
        study_minutes += (number(exact) / 60 if exact is not None else number(row.get("duracao_min"))) + number(extra.get("tempo_video"))
        if extra.get("fonte_questoes") != "Anki":
            questions += number(extra.get("q_certas")) + number(extra.get("q_erradas"))

    study_days = sum("estudo" in categories for categories in days.values())
    workout_days = sum("treino" in categories for categories in days.values())
    achievements = [
        ("01", "Primeiro passo", "Registre sua primeira atividade", len(days), 1),
        ("07", "Construindo o ritmo", "Acumule 7 dias com atividades", len(days), 7),
        ("10", "Mente em movimento", "Estude em 10 dias diferentes", study_days, 10),
        ("10", "Corpo em movimento", "Treine em 10 dias diferentes", workout_days, 10),
        ("30", "Uma nova rotina", "Acumule 30 dias com atividades", len(days), 30),
    ]
    return dict(today=today, days=days, xp=xp, level=xp // 250 + 1, level_xp=xp % 250,
                streak=streak, week=week, week_days=sum(day in days for day in week),
                week_workouts=week_workouts, study_minutes=study_minutes, questions=int(questions),
                today_categories=days.get(today, set()), today_xp=daily_xp(days.get(today, set())),
                achievements=achievements, recent=sorted(valid, key=lambda item: (item[0], str(item[2].get("horario", ""))), reverse=True)[:5])
