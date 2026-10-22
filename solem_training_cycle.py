"""Versioned four-week cycle: read-only goals, never rewrites recorded sessions."""
import json
from datetime import date, timedelta
from pathlib import Path
from statistics import median
from math import floor
from solem_progress import category_of, extras_of, number, record_date

CYCLE = json.loads((Path(__file__).parent / "assets/weekly_training_plan.json").read_text(encoding="utf8"))["cycle"]
START = date.fromisoformat(CYCLE["starts_on"])
END = START + timedelta(days=27)


def clean_rows(records):
    seen, result = set(), []
    for row in records:
        identity = row.get("id")
        if identity is not None and identity in seen:
            continue
        seen.add(identity) if identity is not None else None
        if category_of(row) == "treino" and record_date(row.get("data")):
            result.append(row)
    return result


def amount(row, field):
    raw = extras_of(row.get("dados_extras")).get(field) if field == "isometria_segundos" else row.get(field)
    return max(0, number(raw))


def baseline(rows, spec):
    samples = []
    for row in rows:
        when = record_date(row.get("data"))
        sets = number(row.get("series"))
        if row.get("exercicio") == spec["exercise"] and START-timedelta(days=28) <= when < START and 2 <= sets <= 8 and sets == int(sets):
            value = amount(row, spec["field"]) / sets
            if 0 < value <= (180 if spec["unit"] == "seg" else 30):
                samples.append(value)
    estimate = median(samples) if len(samples) >= 2 else None
    target = spec["per_set"][0]
    if spec["history"] and estimate is not None:
        target = max(spec["minimum"], min(spec["maximum"], floor(estimate * .8)))
    return target, len(samples), estimate


def goals_at(rows, day, stage):
    goals = []
    for key in CYCLE["days"][day.weekday()]["exercises"]:
        spec = CYCLE["exercises"][key]
        base, count, estimate = baseline(rows, spec)
        fallback = key == "pull" and (estimate is None or estimate * .8 < 3)
        if fallback:
            spec = CYCLE["exercises"]["row"]
            base, count, estimate = baseline(rows, spec)
        per_set = base + spec["per_set"][stage] - spec["per_set"][0]
        sets = spec["sets"][stage]
        target = sets * per_set
        names = ("Caminhada", "Corrida") if key == "walk" else (spec["exercise"],)
        value = sum(amount(r, spec["field"]) for r in rows if r.get("exercicio") in names and record_date(r.get("data")) == day)
        goals.append(dict(spec, id=key, target=target, value=value, sets=sets, per_set=per_set,
                          history_days=count, fraction=min(1, value / target), fallback=fallback))
    return goals


def cycle_day(records, day):
    rows = clean_rows(records)
    index = (day-START).days // 7
    weekday = CYCLE["days"][day.weekday()]
    if not 0 <= index < 4:
        return dict(cycle=True, active=False, completed=day>END, recovery=False, goals=[], percent=None,
                    title="Ciclo concluído · revise antes de reiniciar" if day>END else "Ciclo começa em 22/10",
                    duration="", week=day-timedelta(days=day.weekday()), cycle_week=0, stage=0, held=False)
    stage = 0
    for previous_week in range(index):
        first = START + timedelta(days=previous_week*7)
        achieved = 0
        for offset in range(7):
            when = first + timedelta(days=offset)
            goals = goals_at(rows, when, stage)
            if when.weekday() in (0, 2, 4) and goals and all(g["fraction"] >= .8 for g in goals):
                achieved += 1
        if achieved >= 2:
            stage = min(2, stage+1)
    if index == 3:
        stage = 3  # Recovery week is never replaced by another overload week.
    goals = goals_at(rows, day, stage)
    pct = floor(sum(g["fraction"] for g in goals)/len(goals)*100+1e-7) if goals else None
    return dict(cycle=True, active=True, completed=False, recovery=not goals, goals=goals, percent=pct,
                title=weekday["title"], duration=weekday["minutes"], week=day-timedelta(days=day.weekday()),
                cycle_week=index+1, stage=stage+1, phase=CYCLE["labels"][stage], held=stage<index)


def cycle_base_goals(records, day):
    return [dict(id=g["base_id"], label={"flexao":"Flexões", "agachamento":"Agachamentos", "cardio":"Caminhada ou corrida"}[g["base_id"]],
                 value=g["value"], target=g["target"], unit=g["unit"], page="Treino", exercise=g["exercise"])
            for g in cycle_day(records, day)["goals"] if g["base_id"]]
