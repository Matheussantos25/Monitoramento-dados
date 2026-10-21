from datetime import date
from pathlib import Path
import ast
import json

from solem_health import MEAL_TYPES, meal_food_options
from solem_meal_analysis import day_nutrition
from solem_calendar import daily_events


def test_sweet_potato_available_for_every_meal_on_web_and_android():
    root = Path(__file__).resolve().parents[1]
    source = ast.parse((root / "app.py").read_text(encoding="utf8"))
    catalog = next(ast.literal_eval(node.value) for node in source.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "ALIMENTOS_SAUDAVEIS" for t in node.targets))
    android = json.loads((root / "android-app/app/src/main/assets/catalog.json").read_text(encoding="utf8"))
    assert "Batata-doce" in catalog and "Batata-doce" in android["ALIMENTOS_SAUDAVEIS"]
    assert "Macaxeira" in catalog and "Macaxeira" in android["ALIMENTOS_SAUDAVEIS"]
    for meal in MEAL_TYPES:
        assert "Batata-doce" in meal_food_options(meal, catalog)
        assert "Cuscuz" in meal_food_options(meal, catalog)
        assert "Macaxeira" in meal_food_options(meal, catalog)
        if meal in android["MEAL_FOODS"]:
            assert "Batata-doce" in android["MEAL_FOODS"][meal]
            assert "Cuscuz" in android["MEAL_FOODS"][meal]
            assert "Macaxeira" in android["MEAL_FOODS"][meal]


def test_skipped_meal_is_explicit_in_calendar_not_missing_nutrition():
    entry = dict(kind="meal", day="2026-10-19", logged_at="08:00:00",
                 details=dict(tipo_refeicao="Café da manhã", sem_refeicao=True, saudaveis=[], ocasionais=[]))
    assert daily_events([], [entry], date(2026, 10, 19))[0]["detail"] == "Sem refeição — não comi"
    assert day_nutrition([entry])["partial"] is False
    assert day_nutrition([entry])["counted"] == 0


def test_skip_save_edit_and_empty_meal_validation(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("SOLEM_DEMO", "1")
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
    app.radio(key="solem_page").set_value("Saúde").run()
    app.date_input(key="health_day").set_value(date(2026, 10, 19)).run()
    app.selectbox(key="new_meal_type").set_value("Café da manhã").run()
    next(b for b in app.button if b.label == "Salvar refeição").click().run()
    assert any("Selecione um alimento" in e.value for e in app.error)
    app.checkbox(key="meal_skipped_new_2026-10-19_Café da manhã").check().run()
    next(b for b in app.button if b.label == "Salvar refeição").click().run()
    assert not app.exception
    saved = app.session_state["demo_health_entries"]
    assert len(saved) == 1 and saved[0]["details"]["sem_refeicao"] is True
    assert saved[0]["details"]["saudaveis"] == []
    assert next(m for m in app.metric if m.label == "Refeições").value == "0"
    identity = saved[0]["id"]
    app.checkbox(key=f"meal_skipped_{identity}").uncheck().run()
    app.multiselect(key=f"meal_good_{identity}").set_value(["Batata-doce"]).run()
    next(b for b in app.button if b.label == "Salvar edição").click().run()
    assert not app.exception
    saved = app.session_state["demo_health_entries"]
    assert len(saved) == 1 and saved[0]["details"]["sem_refeicao"] is False
    assert saved[0]["details"]["saudaveis"] == ["Batata-doce"]
    assert next(m for m in app.metric if m.label == "Refeições").value == "1"
    app.checkbox(key=f"meal_skipped_{identity}").check().run()
    next(b for b in app.button if b.label == "Salvar edição").click().run()
    assert saved[0]["details"]["saudaveis"] == []
    app.selectbox(key="new_meal_type").set_value("Almoço").run()
    assert not app.checkbox(key="meal_skipped_new_2026-10-19_Almoço").value
    app.checkbox(key="meal_skipped_new_2026-10-19_Almoço").check().run()
    next(b for b in app.button if b.label == "Salvar refeição").click().run()
    assert not app.exception
    assert len(app.session_state["demo_health_entries"]) == 2
