"""Read-only daily goals from existing workout, study and private-health entries.

The values are derived on each render; this module does not award XP or write
to Supabase. ``None`` for private entries means unavailable, not zero intake.
"""
from solem_progress import category_of, extras_of, number, record_date


def daily_checkup(records, private_entries, day):
    reps = questions = 0
    study_minutes = 0.0
    for row in records:
        if record_date(row.get("data")) != day:
            continue
        category = category_of(row)
        extra = extras_of(row.get("dados_extras"))
        if category == "treino":
            reps += int(number(row.get("repeticoes")))
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
        {"id": "reps", "label": "Repetições", "value": reps, "target": 200,
         "unit": "rep", "page": "Treino"},
        {"id": "questions", "label": "Questões", "value": questions, "target": 150,
         "unit": "questões", "page": "Estudar"},
        {"id": "study", "label": "Tempo de estudo", "value": int(study_minutes),
         "target": 60, "unit": "min", "page": "Estudar"},
    )
    return [{**goal, "done": goal["value"] is not None and goal["value"] >= goal["target"]}
            for goal in goals]
