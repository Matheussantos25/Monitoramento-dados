"""Read-only activity journal derived from the existing treinos history."""
from calendar import monthrange
from datetime import date
from solem_progress import category_of, extras_of, number, record_date


def monthly_activity(records, year, month, today=None):
    today = today or date.today()
    days = {date(year, month, n): {"study": False, "workout": False,
        "study_minutes": 0.0, "workout_minutes": 0.0, "reps": 0,
        "distance": 0.0, "activities": []} for n in range(1, monthrange(year, month)[1]+1)}
    for row in records:
        day = record_date(row.get("data"))
        if day not in days or day > today:
            continue
        category = category_of(row)
        if category not in ("estudo", "treino"):
            continue
        item = days[day]
        extras = extras_of(row.get("dados_extras"))
        if category == "estudo":
            item["study"] = True
            exact = extras.get("tempo_segundos_exato")
            item["study_minutes"] += (number(exact)/60 if exact is not None else number(row.get("duracao_min"))) + number(extras.get("tempo_video"))
        else:
            item["workout"] = True
            item["workout_minutes"] += number(row.get("duracao_min")) + number(extras.get("isometria_segundos"))/60
            item["reps"] += int(number(row.get("repeticoes")))
            item["distance"] += number(row.get("distancia_km"))
        item["activities"].append(str(row.get("exercicio") or "Atividade"))
    return days


def latest_weight(records, today):
    valid = [r for r in records if record_date(r.get("data")) is not None
             and record_date(r.get("data")) <= today and number(r.get("peso_corporal")) > 0]
    if not valid:
        return None
    row = max(valid, key=lambda r: (record_date(r["data"]), str(r.get("horario") or ""), number(r.get("id"))))
    return number(row["peso_corporal"]), record_date(row["data"])
