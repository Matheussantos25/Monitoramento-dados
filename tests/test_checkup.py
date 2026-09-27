from datetime import date

from solem_calendar import daily_events
from solem_checkup import daily_checkup


DAY = date(2026, 9, 27)


def row(group, exercise, **values):
    return {"data": str(DAY), "horario": "08:30:00", "grupo_muscular": group,
            "exercicio": exercise, "repeticoes": 0, "duracao_min": 0,
            "dados_extras": {}, **values}


def test_checkup_recomputes_from_existing_entries_and_ignores_other_days():
    records = [row("Peitoral", "Flexão", repeticoes=120),
               row("Pernas", "Agachamento", repeticoes=80),
               row("Estudos", "Língua Portuguesa", repeticoes=100, duracao_min=35),
               row("Estudos", "Matemática", repeticoes=50, duracao_min=25),
               row("Estudos", "Anki", repeticoes=300, duracao_min=10,
                   dados_extras={"fonte_questoes": "Anki"}),
               {**row("Peitoral", "Flexão", repeticoes=500), "data": "2026-09-26"}]
    water = [{"day": str(DAY), "kind": "water", "details": {"volume_ml": 750, "quantidade": 4}},
             {"day": "2026-09-26", "kind": "water", "details": {"volume_ml": 2000, "quantidade": 2}}]
    goals = {goal["id"]: goal for goal in daily_checkup(records, water, DAY)}
    assert {name: goal["value"] for name, goal in goals.items()} == {
        "water": 3000, "reps": 200, "questions": 150, "study": 70}
    assert all(goal["done"] for goal in goals.values())


def test_private_diary_failure_is_not_reported_as_zero_water():
    goals = {goal["id"]: goal for goal in daily_checkup([], None, DAY)}
    assert goals["water"]["value"] is None
    assert not goals["water"]["done"]
    assert goals["reps"]["value"] == 0


def test_calendar_day_lists_workout_study_and_private_health_details():
    records = [row("Peitoral", "Flexão", repeticoes=25),
               row("Estudos", "Português", repeticoes=12, duracao_min=20),
               row("Nutrição", "Refeição Diária", alimentacao_saudavel="Banana")]
    private = [{"day": str(DAY), "logged_at": "09:10:00", "kind": "water",
                "details": {"volume_ml": 750, "quantidade": 2}},
               {"day": str(DAY), "logged_at": "23:00:00", "kind": "sleep",
                "details": {"duracao_min": 480}}]
    events = daily_events(records, private, DAY)
    assert len(events) == 5
    assert any(event["title"] == "Água" and event["detail"] == "1500 ml" for event in events)
    assert any(event["title"] == "Flexão" and "25 rep" in event["detail"] for event in events)
    assert any(event["title"] == "Português" and "12 questões" in event["detail"] for event in events)
