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


def daily_events(records, private_entries, day):
    """Timeline for one selected calendar day; content is rendered as text in JS."""
    events = []
    for row in records:
        if record_date(row.get("data")) != day:
            continue
        category = category_of(row)
        extra = extras_of(row.get("dados_extras"))
        facts = []
        if category == "treino":
            reps = int(number(row.get("repeticoes")))
            if reps: facts.append(f"{reps} rep")
            seconds = int(number(extra.get("isometria_segundos")))
            if seconds: facts.append(f"{seconds} seg sustentados")
            minutes = number(row.get("duracao_min"))
            if minutes: facts.append(f"{minutes:g} min")
            km = number(row.get("distancia_km"))
            if km: facts.append(f"{km:g} km")
            label = "Treino"
        elif category == "estudo":
            exact = extra.get("tempo_segundos_exato")
            minutes = (number(exact) / 60 if exact is not None
                       else number(row.get("duracao_min"))) + number(extra.get("tempo_video"))
            if minutes: facts.append(f"{minutes:g} min")
            if extra.get("fonte_questoes") == "Anki":
                cards = int(number(row.get("repeticoes")))
                if cards: facts.append(f"{cards} cartões")
            else:
                questions = int(number(row.get("repeticoes")))
                if questions: facts.append(f"{questions} questões")
            label = "Estudo"
        elif category == "alimentação":
            food = [str(row.get(key) or "").strip() for key in
                    ("alimentacao_saudavel", "alimentacao_besteirol")]
            facts = [part for part in food if part]
            label = "Alimentação"
        elif row.get("grupo_muscular") == "Métricas" and number(row.get("peso_corporal")) > 0:
            facts = [f"{number(row.get('peso_corporal')):g} kg"]
            label = "Peso"
        else:
            continue
        events.append({"time": str(row.get("horario") or "")[:5], "kind": label,
                       "title": str(row.get("exercicio") or label), "detail": " · ".join(facts)})

    for entry in private_entries or []:
        if record_date(entry.get("day")) != day:
            continue
        details = entry.get("details") or {}
        kind = entry.get("kind")
        if kind == "water":
            amount = round(number(details.get("volume_ml")) * number(details.get("quantidade")))
            label, title, detail = "Saúde", "Água", f"{amount} ml" if amount else "Registro de água"
        elif kind == "meal":
            foods = [food for key in ("saudaveis", "ocasionais")
                     for food in (details.get(key) if isinstance(details.get(key), list) else [])]
            label, title, detail = "Saúde", str(details.get("tipo_refeicao") or "Refeição"), ", ".join(map(str, foods))
        elif kind == "sleep":
            minutes = int(number(details.get("duracao_min")))
            label, title, detail = "Saúde", "Sono", f"{minutes // 60} h {minutes % 60:02} min" if minutes else "Sono registrado"
        elif kind == "weight":
            label, title, detail = "Saúde", "Peso corporal", f"{number(details.get('kg')):g} kg"
        else:
            continue
        events.append({"time": str(entry.get("logged_at") or "")[:5],
                       "kind": label, "title": title, "detail": detail})
    return sorted(events, key=lambda item: (item["time"], item["kind"], item["title"]))
