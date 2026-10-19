from datetime import date, timedelta
from pathlib import Path
import json
import pytest
from solem_health import sleep_period
from solem_training_plan import PLAN, plan_day, workout_day

DAY = date(2026, 10, 19)


def row(identity, day=DAY, exercise="Abdominal Levantada", reps=12, seconds=0, group="Abdominal"):
    return dict(id=identity, data=str(day), horario="08:00:00", exercicio=exercise,
                grupo_muscular=group, repeticoes=reps, dados_extras={"isometria_segundos": seconds})


def test_same_day_sleep_and_explicit_dates():
    result = sleep_period(DAY, "02:00", "08:00")
    assert result == dict(dormir="02:00", acordar="08:00", duracao_min=360,
                          dormiu_em="2026-10-19", acordou_em="2026-10-19")
    assert sleep_period(DAY, "01:00", "08:00", "same")["duracao_min"] == 420
    assert sleep_period(date(2027, 1, 1), "23:00", "07:00")["dormiu_em"] == "2026-12-31"
    assert sleep_period(date(2024, 3, 1), "23:00", "07:00")["dormiu_em"] == "2024-02-29"
    assert sleep_period(DAY, "23:00", "07:00", "previous")["duracao_min"] == 480


@pytest.mark.parametrize("bed,wake,mode", [("23:00", "07:00", "same"), ("02:00", "08:00", "previous"),
    ("08:00", "08:00", "auto"), ("25:00", "08:00", "auto"), ("00:00", "17:00", "same")])
def test_impossible_sleep_rejected_without_silent_wrap(bed, wake, mode):
    with pytest.raises(ValueError): sleep_period(DAY, bed, wake, mode)


def test_plan_config_matches_android_and_uses_existing_exercises():
    root = Path(__file__).resolve().parents[1]
    for folder in ("assets", "test/resources"):
        location = "main/assets" if folder == "assets" else folder
        assert json.loads((root / "android-app/app/src" / location / "weekly_training_plan.json").read_text(encoding="utf8")) == PLAN
    from solem_health import WORKOUT_EXERCISE_PROFILES
    assert all(e["exercise"] in WORKOUT_EXERCISE_PROFILES for e in PLAN["exercises"].values())
    assert not {e["exercise"] for e in PLAN["exercises"].values()} & {"Flexão", "Agachamento", "Caminhada", "Corrida", "Mewing com borracha"}


def test_current_week_never_moves_target_and_future_history_is_ignored():
    history = [row(1, DAY-timedelta(days=3), reps=20), row(2, DAY-timedelta(days=5), reps=40)]
    before = plan_day(history, DAY)
    after = plan_day(history+[row(3, reps=900), row(4, DAY+timedelta(days=20), reps=1000)], DAY)
    assert before["goals"][0]["target"] == 20
    assert [g["target"] for g in before["goals"]] == [g["target"] for g in after["goals"]]
    assert after["percent"] == 50  # Excess abs never compensate missing plank.


def test_separate_base_progress_and_real_sessions_edit_delete_recalculation():
    from solem_journey import preferences
    settings = preferences(personal=True)
    a, b = row(1, reps=6), row(2, reps=6)
    plank = row(3, exercise="Prancha", reps=2, seconds=30)
    assert plan_day([a,b,plank], DAY)["percent"] == 100
    assert plan_day([a,plank], DAY)["percent"] == 75
    a["repeticoes"] = 3
    assert plan_day([a,plank], DAY)["percent"] == 62
    output = workout_day([a,b,plank, row(9, exercise="Matemática", group="Estudos")], DAY, settings)
    assert output["base_pct"] == 0
    assert len(output["events"]) == 3
    assert all(e["kind"] == "Treino" for e in output["events"])
    assert settings["targets"]["agachamento"] == 100


def test_plank_uses_seconds_not_repetition_count_and_deduplicates():
    plank = row(1, exercise="Prancha", reps=999, seconds=15)
    assert plan_day([plank,plank], DAY)["percent"] == 25


def test_recovery_prelaunch_new_accounts_and_future_are_not_fake_completion():
    assert plan_day([], DAY)["percent"] == 0
    assert plan_day([], DAY+timedelta(days=2))["recovery"]
    assert plan_day([], DAY+timedelta(days=2))["percent"] is None
    assert not plan_day([], DAY-timedelta(days=1))["active"]
    assert not plan_day([], DAY, enabled=False)["active"]
    future = workout_day([row(1, DAY+timedelta(days=1))], DAY+timedelta(days=1), now=DAY)
    assert future["base_pct"] is None and future["plan_pct"] is None and future["events"] == []


def test_sleep_form_saves_morning_sleep_on_correct_day_and_switches_cleanly():
    import os
    from unittest.mock import patch
    from streamlit.testing.v1 import AppTest
    with patch.dict(os.environ, {"SOLEM_DEMO": "1"}):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=40).run()
        app.radio(key="solem_page").set_value("Saúde").run()
        app.date_input(key="health_day").set_value(DAY).run()
        next(t for t in app.text_input if t.label == "Horário em que dormiu").set_value("02:00").run()
        next(t for t in app.text_input if t.label == "Horário em que acordou").set_value("08:00").run()
        next(r for r in app.radio if r.label == "Quando começou o sono?").set_value("same").run()
        next(b for b in app.button if b.label == "Salvar sono").click().run()
        assert not app.exception
        saved = next(r for r in app.session_state["demo_health_entries"] if r["kind"] == "sleep")
        assert saved["day"] == "2026-10-19" and saved["details"]["duracao_min"] == 360
        assert saved["details"]["dormiu_em"] == "2026-10-19"
        app.date_input(key="health_day").set_value(DAY-timedelta(days=1)).run()
        assert next(t for t in app.text_input if t.label == "Horário em que dormiu").value == "23:00"
        app.date_input(key="health_day").set_value(DAY).run()
        assert next(t for t in app.text_input if t.label == "Horário em que dormiu").value == "02:00"
        next(t for t in app.text_input if t.label == "Horário em que dormiu").set_value("01:00").run()
        next(b for b in app.button if b.label == "Salvar edição do sono").click().run()
        assert len(app.session_state["demo_health_entries"]) == 1
        assert app.session_state["demo_health_entries"][0]["details"]["duracao_min"] == 420


def test_sleep_text_accepts_midnight_and_any_minute_rejects_invalid(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("SOLEM_DEMO", "1")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=40).run()
    app.radio(key="solem_page").set_value("Saúde").run()
    app.date_input(key="health_day").set_value(DAY).run()
    next(r for r in app.radio if r.label == "Quando começou o sono?").set_value("same").run()
    for bedtime in ("00:00", "01:00", "02:07"):
        next(t for t in app.text_input if t.label == "Horário em que dormiu").set_value(bedtime).run()
        assert not app.exception
        assert not next(b for b in app.button if b.label == "Salvar sono").disabled
    for invalid in ("", "24:00", "02:60", "abc"):
        next(t for t in app.text_input if t.label == "Horário em que dormiu").set_value(invalid).run()
        assert not app.exception
        assert next(b for b in app.button if b.label == "Salvar sono").disabled
        assert any("HH:MM" in w.value for w in app.warning)
    assert app.session_state["demo_health_entries"] == []


def test_plan_shortcut_prefills_exercise_and_does_not_write_fake_activity():
    import os
    from unittest.mock import patch
    from streamlit.testing.v1 import AppTest
    with patch.dict(os.environ, {"SOLEM_DEMO":"1", "SOLEM_DEMO_PROFILE":"personal"}):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"), default_timeout=40).run()
        original = list(app.session_state["solem_demo_records"])
        buttons = [b for b in app.button if b.key and b.key.startswith("plan_register_")]
        if buttons:  # No shortcut on a recovery day.
            name = buttons[0].label.removeprefix("Registrar ")
            buttons[0].click().run()
            assert app.selectbox(key="treino_exercicio").value == name
            assert app.session_state["solem_demo_records"] == original
        assert not app.exception
