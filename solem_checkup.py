"""Read-only daily goals from existing workout, study and private-health entries.

The values are derived on each render; this module does not award XP or write
to Supabase. ``None`` for private entries means unavailable, not zero intake.
"""
from solem_progress import category_of, extras_of, number, record_date


def daily_checkup(records, private_entries, day, generic=False, preferences=None, creator_items=None):
    questions = 0
    study_minutes = 0.0
    exercise_totals = {"Mewing com borracha": 0, "Flexão": 0, "Agachamento": 0}
    cardio_km = 0.0
    for row in records:
        if record_date(row.get("data")) != day:
            continue
        category = category_of(row)
        extra = extras_of(row.get("dados_extras"))
        if category == "treino":
            exercise = row.get("exercicio")
            if exercise in exercise_totals:
                exercise_totals[exercise] += int(number(row.get("repeticoes")))
            if exercise in ("Caminhada", "Corrida"):
                cardio_km += max(0, number(row.get("distancia_km")))
        elif category == "estudo":
            exact = extra.get("tempo_segundos_exato")
            study_minutes += (number(exact) / 60 if exact is not None
                              else number(row.get("duracao_min"))) + number(extra.get("tempo_video"))
            if extra.get("fonte_questoes") != "Anki":
                questions += int(number(row.get("repeticoes")))

    water_ml = None
    if private_entries is not None:
        water_ml = 0
        for entry in private_entries:
            if entry.get("kind") != "water" or record_date(entry.get("day")) != day:
                continue
            details = entry.get("details") or {}
            volume = number(details.get("volume_ml"))
            count = number(details.get("quantidade"))
            if 0 < volume <= 5000 and 0 < count <= 50:
                water_ml += round(volume * count)

    goals = (
        {"id": "water", "label": "Água", "value": water_ml, "target": 3000,
         "unit": "ml", "page": "Saúde"},
        {"id": "mewing", "label": "Mewing com borracha", "value": exercise_totals["Mewing com borracha"],
         "target": 400, "unit": "rep", "page": "Treino"},
        {"id": "flexao", "label": "Flexões", "value": exercise_totals["Flexão"],
         "target": 50, "unit": "rep", "page": "Treino"},
        {"id": "agachamento", "label": "Agachamentos", "value": exercise_totals["Agachamento"],
         "target": 50, "unit": "rep", "page": "Treino"},
        {"id": "cardio", "label": "Caminhada ou corrida", "value": round(cardio_km, 2),
         "target": 5, "unit": "km", "page": "Treino"},
        {"id": "questions", "label": "Questões", "value": questions, "target": 150,
         "unit": "questões", "page": "Estudar"},
        {"id": "study", "label": "Tempo de estudo", "value": int(study_minutes),
         "target": 60, "unit": "min", "page": "Estudar"},
    )
    if generic:
        from solem_account import DEFAULTS
        goals = [{**goal, "target": DEFAULTS["checkup_targets"][goal["id"]]}
                 for goal in goals if goal["id"] != "mewing"]
    if preferences is not None:
        from solem_journey import creator_progress
        stats = creator_progress(creator_items, day) if creator_items is not None else None
        goals = list(goals) + [
            {"id": key, "label": label, "value": stats[key] if stats is not None else None,
             "target": 2, "unit": "vídeos", "page": "Criador"}
            for key, label in (("created", "Vídeos criados"), ("published", "Vídeos publicados"))
        ]
        goals = [{**g, "target": preferences["targets"][g["id"]]}
                 for g in goals if g["id"] in preferences["enabled"]]
    return [{**goal, "done": goal["value"] is not None and goal["value"] >= goal["target"]}
            for goal in goals]
