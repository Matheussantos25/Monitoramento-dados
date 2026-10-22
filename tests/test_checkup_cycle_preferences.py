"""Regression: the four-week plan must not override the user's checklist."""
from copy import deepcopy
from datetime import date
from pathlib import Path
import pytest
from solem_checkup import daily_checkup
from solem_journey import preferences
from solem_training_plan import workout_day


@pytest.mark.parametrize("day", [date(2026,10,21),date(2026,10,22),date(2026,10,23),
    date(2026,10,24),date(2026,11,19)])
def test_screenshot_five_missions_remain_visible_with_exact_saved_values(day):
    prefs=preferences({"enabled":["water","flexao","agachamento","cardio","published"],
                       "targets":{"flexao":50,"agachamento":100,"cardio":5}},personal=True)
    before=deepcopy(prefs)
    rows=[dict(id=1,data=str(day),grupo_muscular="Peito",exercicio="Flexão",repeticoes=20),
          dict(id=2,data=str(day),grupo_muscular="Pernas",exercicio="Agachamento",repeticoes=40),
          dict(id=3,data=str(day),grupo_muscular="Cardio",exercicio="Caminhada",distancia_km=.61)]
    original=deepcopy(rows)
    goals=daily_checkup(rows,[],day,preferences=prefs,creator_items=[])
    assert [g["id"] for g in goals] == prefs["enabled"]
    assert {g["id"]:g["target"] for g in goals} == dict(water=3000,flexao=50,agachamento=100,cardio=5,published=2)
    assert {g["id"]:g["value"] for g in goals} == dict(water=0,flexao=20,agachamento=40,cardio=.61,published=0)
    assert rows == original and prefs == before


@pytest.mark.parametrize("enabled", [[],["water"],["flexao"],["agachamento"],["cardio"],["mewing"],
    ["questions","study","published"]])
def test_cycle_never_reenables_a_disabled_mission(enabled):
    prefs=preferences({"enabled":enabled},personal=True)
    for day in (date(2026,10,22),date(2026,10,23),date(2026,10,24)):
        assert {g["id"] for g in daily_checkup([],[],day,preferences=prefs)} == set(enabled)


def test_calendar_cycle_base_is_independent_of_checkup_visibility():
    day=date(2026,10,22)
    rows=[dict(id=1,data=str(day),horario="08:00:00",grupo_muscular="Cardio",exercicio="Caminhada",distancia_km=5)]
    prefs=preferences({"enabled":["water"],"targets":{"cardio":10}},personal=True)
    assert [g["id"] for g in daily_checkup(rows,[],day,preferences=prefs)] == ["water"]
    result=workout_day(rows,day,prefs,False,day)
    assert result["base_pct"] == result["plan_pct"] == 100


def test_saving_settings_then_returning_to_overview_shows_all_selected_goals(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("SOLEM_DEMO","1")
    monkeypatch.setenv("SOLEM_DEMO_PROFILE","personal")
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=40).run()
    original=deepcopy(app.session_state["solem_demo_records"])
    app.radio(key="solem_page").set_value("Metas e aparência").run()
    enabled=["water","flexao","agachamento","cardio","published"]
    app.multiselect(key="journey_enabled").set_value(enabled)
    app.number_input(key="target_flexao").set_value(50)
    app.number_input(key="target_agachamento").set_value(100)
    next(b for b in app.button if b.label == "Salvar minhas metas").click().run()
    app.radio(key="solem_page").set_value("Visão geral").run()
    assert not app.exception
    prefs=app.session_state["journey_preferences"]
    assert prefs["enabled"] == enabled and prefs["targets"]["flexao"] == 50
    rendered="\n".join(x.proto.body for x in app.get("html"))
    for label in ("Água","Flexões","Agachamentos","Caminhada ou corrida","Vídeos publicados"):
        assert label in rendered
    assert app.session_state["solem_demo_records"] == original
