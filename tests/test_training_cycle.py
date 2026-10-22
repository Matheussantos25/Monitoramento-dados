from copy import deepcopy
from datetime import timedelta
from solem_training_cycle import START, END, CYCLE, cycle_day, goals_at, clean_rows
from solem_training_plan import plan_day, workout_day
from solem_checkup import daily_checkup


def record(identity, day, exercise, reps=0, sets=3, seconds=0, km=0):
    return dict(id=identity, data=str(day), horario="08:00:00", grupo_muscular="Treino",
                exercicio=exercise, repeticoes=reps, series=sets, distancia_km=km,
                dados_extras={"isometria_segundos": seconds})


def completed_week(rows, week, stage):
    result = list(rows)
    first = START+timedelta(days=week*7)
    for offset in range(7):
        when = first+timedelta(days=offset)
        for goal in goals_at(clean_rows(rows), when, stage):
            result.append(record(len(result)+1, when, goal["exercise"],
                                 reps=goal["target"] if goal["unit"] == "rep" else 0,
                                 sets=goal["sets"], seconds=goal["target"] if goal["unit"] == "seg" else 0,
                                 km=goal["target"] if goal["unit"] == "km" else 0))
    return result


def test_cycle_respects_reported_session_capacity_and_counts_existing_walk():
    day = START+timedelta(days=1)  # Friday
    result = cycle_day([],day)
    by_name = {g["exercise"]:g for g in result["goals"]}
    assert (by_name["Flexão"]["sets"],by_name["Flexão"]["per_set"]) == (3,8)
    assert by_name["Agachamento"]["target"] == 45
    assert by_name["Flexão"]["rest_seconds"] == 120
    walk = cycle_day([record(1,START,"Caminhada",km=2),record(2,START,"Corrida",km=3)],START)
    assert walk["percent"] == 100 and walk["goals"][0]["target"] == 5


def test_daily_aggregates_are_not_session_capacity_and_future_data_does_not_change_goals():
    day = START+timedelta(days=6)  # Wednesday: pull fallback
    rows = [record(1,START-timedelta(days=2),"Barra Fixa (Pronada)",100,1),
            record(2,START-timedelta(days=1),"Barra Fixa (Pronada)",100,1)]
    result = cycle_day(rows,day)
    assert "Barra Fixa (Pronada)" not in [g["exercise"] for g in result["goals"]]
    assert any(g["fallback"] for g in result["goals"])
    after = cycle_day(rows+[record(3,day,"Flexão",999),record(4,END+timedelta(days=1),"Flexão",999)],day)
    assert [g["target"] for g in result["goals"]] == [g["target"] for g in after["goals"]]


def test_series_history_used_without_writing_or_hiding_records():
    rows = [record(i,START-timedelta(days=i),"Barra Fixa (Pronada)",15,3) for i in (1,2)]
    original = deepcopy(rows)
    result = cycle_day(rows,START+timedelta(days=6))
    pull = next(g for g in result["goals"] if g["exercise"] == "Barra Fixa (Pronada)")
    assert pull["per_set"] == 4 and pull["history_days"] == 2
    assert rows == original
    assert cycle_day(rows+rows,START+timedelta(days=6)) == result
    # Low recorded capacity lowers the conservative defaults rather than forcing more.
    low = [record(i,START-timedelta(days=i),"Abdominal Levantada",15,3) for i in (1,2)]
    assert next(g for g in cycle_day(low,START+timedelta(days=1))["goals"] if g["id"] == "core")["per_set"] == 4


def test_progression_requires_previous_week_and_week_four_deloads_even_when_held():
    held = cycle_day([],START+timedelta(days=8))
    assert held["stage"] == 1 and held["held"]
    rows = completed_week([],0,0)
    advanced = cycle_day(rows,START+timedelta(days=8))
    assert advanced["stage"] == 2 and not advanced["held"]
    assert next(g for g in advanced["goals"] if g["id"] == "push")["target"] == 27
    rows = completed_week(rows,1,1)
    peak = cycle_day(rows,START+timedelta(days=15))
    assert peak["stage"] == 3
    assert next(g for g in peak["goals"] if g["id"] == "push")["target"] == 32
    for history in ([],rows):
        deload = cycle_day(history,START+timedelta(days=22))
        assert deload["stage"] == 4
        assert next(g for g in deload["goals"] if g["id"] == "push")["target"] == 16


def test_recovery_end_and_generic_accounts_do_not_receive_personal_cycle():
    assert cycle_day([],START+timedelta(days=2))["percent"] is None
    assert cycle_day([],END+timedelta(days=1))["completed"]
    assert cycle_day([],END+timedelta(days=1))["goals"] == []
    assert not plan_day([],START,enabled=False).get("cycle")
    assert not plan_day([],START-timedelta(days=1)).get("cycle")
    generic = daily_checkup([],[],START+timedelta(days=1),generic=True)
    assert not any(g["target"] == 24 for g in generic if g["id"] == "flexao")


def test_checkup_uses_saved_targets_while_calendar_keeps_cycle_targets():
    from solem_journey import preferences
    settings = preferences(personal=True)
    original = deepcopy(settings)
    day = START+timedelta(days=1)
    rows = [record(1,day,"Flexão",24),record(2,day,"Agachamento",45)]
    goals = daily_checkup(rows,[],day,preferences=settings)
    physical = {g["id"]:g for g in goals if g["page"] == "Treino"}
    assert set(physical) == {"mewing","flexao","agachamento","cardio"}
    assert physical["flexao"]["target"] == 100 and physical["agachamento"]["target"] == 100
    assert physical["flexao"]["value"] == 24 and physical["agachamento"]["value"] == 45
    assert not any(g["done"] for g in physical.values())
    result = workout_day(rows,day,settings,False,day)
    assert result["base_pct"] == 100 and result["plan_pct"] < 100
    assert len(result["events"]) == 2
    assert settings == original and settings["targets"]["agachamento"] == 100


def test_cycle_exercises_are_in_both_catalogs():
    import json
    from pathlib import Path
    from solem_health import WORKOUT_EXERCISE_PROFILES
    for spec in CYCLE["exercises"].values():
        assert spec["exercise"] in WORKOUT_EXERCISE_PROFILES
    root=Path(__file__).resolve().parents[1]
    for folder in ("main/assets", "test/resources"):
        shared=json.loads((root/"android-app/app/src"/folder/"weekly_training_plan.json").read_text(encoding="utf8"))
        assert shared["cycle"] == CYCLE


def test_cycle_panel_preview_and_calendar_render_without_writing_records():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string('''
from datetime import date
from solem_training_plan_ui import training_plan_panel
training_plan_panel([],date(2026,10,23))
''',default_timeout=30).run()
    assert not app.exception
    assert any("Semana 1/4" in item.value for item in app.markdown)
    app.selectbox(key="cycle_preview_week").set_value(2).run()
    assert not app.exception
    assert any("4×8 rep" in item.value for item in app.markdown)
    assert any("3×18 rep" in item.value for item in app.markdown)
    assert [b.label for b in app.button if b.key and b.key.startswith("plan_register_")]
