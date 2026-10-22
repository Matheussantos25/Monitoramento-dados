"""Read-only, versioned plans. No writes, invented workouts or inferred 1RM.

Targets use only the 28 days BEFORE the selected week's Monday. Current-week
workouts never move the legacy goalposts. From 22/10 the four-week cycle uses a
fixed pre-cycle baseline instead. The JSON is bundled unchanged in Android.
"""
import json
from datetime import date, timedelta
from pathlib import Path
from statistics import median
from math import floor
from solem_progress import category_of, extras_of, number, record_date
from solem_checkup import daily_checkup
from solem_calendar import daily_events

PLAN = json.loads((Path(__file__).parent / "assets/weekly_training_plan.json").read_text(encoding="utf-8"))


def workout_rows(records):
    seen, result = set(), []
    for row in records:
        identity = row.get("id")
        if identity is not None:
            if identity in seen: continue
            seen.add(identity)
        if category_of(row) == "treino" and record_date(row.get("data")):
            result.append(row)
    return result


def _value(row, field):
    raw = extras_of(row.get("dados_extras")).get(field) if field == "isometria_segundos" else row.get(field)
    return max(0, number(raw))


def plan_day(records, day, enabled=True):
    from solem_training_cycle import START, cycle_day
    if enabled and day >= START:
        return cycle_day(records, day)
    weekday = PLAN["days"][day.weekday()]
    week = day - timedelta(days=day.weekday())
    rows = workout_rows(records)
    goals = []
    active = enabled and day >= date.fromisoformat(PLAN["starts_on"])
    if active:
        for key in weekday["exercises"]:
            spec = PLAN["exercises"][key]
            relevant = [r for r in rows if r.get("exercicio") == spec["exercise"]]
            past = {}
            for row in relevant:
                when = record_date(row["data"])
                if week - timedelta(days=PLAN["lookback_days"]) <= when < week:
                    past[when] = past.get(when, 0) + _value(row, spec["field"])
            values = [v for v in past.values() if v > 0]
            target = (floor(median(values) * PLAN["history_factor"] / spec["step"]) * spec["step"]
                      if len(values) >= 2 else spec["minimum"])
            target = max(spec["minimum"], min(spec["maximum"], target))
            value = sum(_value(r, spec["field"]) for r in relevant if record_date(r["data"]) == day)
            goals.append(dict(spec, id=key, target=target, value=value,
                              history_days=len(values), fraction=min(1, value / target)))
    pct = floor(sum(g["fraction"] for g in goals) / len(goals) * 100 + 1e-7) if goals else None
    return dict(title=weekday["title"], duration=weekday["minutes"], goals=goals,
                percent=pct, active=active, recovery=active and not goals, week=week)


def workout_day(records, day, preferences=None, generic=False, now=None):
    now = now or day
    rows = workout_rows(records)
    base = [g for g in daily_checkup(rows, [], day, generic, preferences)
            if g["page"] == "Treino"]
    from solem_training_cycle import START, cycle_base_goals
    if not generic and day >= START:
        # Calendar B remains the cycle's base, independent of personal checklist
        # settings. Both views read the same sessions; neither creates extra reps.
        base = cycle_base_goals(rows, day)
    future = day > now
    base_pct = floor(sum(min(1, max(0, g["value"]) / g["target"]) for g in base) / len(base) * 100 + 1e-7) if base and not future else None
    plan = plan_day(rows, day, enabled=not generic)
    return dict(date=day.isoformat(), study=False, study_minutes=0,
                workout=not future and any(record_date(r["data"]) == day for r in rows),
                base_pct=base_pct, plan_pct=None if future else plan["percent"],
                plan_status="Futuro" if future else "Recuperação" if plan["recovery"] else "Sem plano" if not plan["active"] else plan["title"],
                events=[] if future else daily_events(rows, [], day))
