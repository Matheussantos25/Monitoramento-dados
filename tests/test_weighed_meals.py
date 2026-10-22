from copy import deepcopy
from streamlit.testing.v1 import AppTest
from solem_meal_analysis import meal_details, day_nutrition

ITEMS = [{"name":"Arroz", "food_id":"169757", "grams":150},
         {"name":"Frango", "food_id":"171477", "grams":100}]

def test_weighed_totals_and_daily_coverage_preserve_legacy():
    details = meal_details("Almoço", ITEMS, weighed=True)
    assert details["input_method"] == "weighed"
    assert details["nutrition"]["totals"]["kcal"] == 360
    assert details["nutrition"]["totals"]["protein_g"] == 35
    rows=[{"details":details},{"details":{"saudaveis":["Arroz"]}},
          {"details":{"sem_refeicao":True}}]
    original=deepcopy(rows)
    totals=day_nutrition(rows)
    assert totals["totals"]["kcal"] == 360 and totals["partial"]
    assert rows == original
    details["nutrition"]["items"][0]["grams"]=100
    assert day_nutrition([{"details":details}])["totals"]["kcal"] == 295

def test_new_weighed_form_save_and_edit():
    code='''
import streamlit as st
from datetime import date
from solem_meal_photo_ui import review_meal
def save(client,day,time,kind,details,message,old=None,demo=False):
    st.session_state.saved=details
review_meal(None,date(2026,10,22),{"items":[]},save,"scale",demo=True,weighed=True)
'''
    app=AppTest.from_string(code).run()
    assert not app.exception
    assert app.button(key="scale_save").disabled
    app.multiselect(key="scale_added").set_value(["169757","171477"]).run()
    app.number_input(key="scale_extra_169757").set_value(150)
    app.number_input(key="scale_extra_171477").set_value(100).run()
    app.checkbox(key="scale_confirmed").check().run()
    app.button(key="scale_save").click().run()
    assert not app.exception
    saved=app.session_state.saved
    assert saved["input_method"] == "weighed"
    assert saved["nutrition"]["totals"]["kcal"] == 360
    assert saved["nutrition"]["totals"]["protein_g"] == 35

def test_health_diary_save_persists_and_edit_recalculates(monkeypatch):
    from pathlib import Path
    monkeypatch.setenv("SOLEM_DEMO", "1")
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=40).run()
    app.radio(key="solem_page").set_value("Saúde").run()
    day=app.date_input(key="health_day").value
    key=f"weighed_meal_{day}"
    app.multiselect(key=f"{key}_added").set_value(["169757","171477"]).run()
    app.number_input(key=f"{key}_extra_169757").set_value(150)
    app.number_input(key=f"{key}_extra_171477").set_value(100).run()
    app.checkbox(key=f"{key}_confirmed").check().run()
    app.button(key=f"{key}_save").click().run()
    assert not app.exception
    rows=app.session_state["demo_health_entries"]
    assert len(rows)==1 and rows[0]["details"]["nutrition"]["totals"]["kcal"]==360
    identity=rows[0]["id"]
    edit=f"meal_nutrition_{identity}"
    app.number_input(key=f"{edit}_grams_0").set_value(100).run()
    app.checkbox(key=f"{edit}_confirmed").check().run()
    app.button(key=f"{edit}_save").click().run()
    assert not app.exception
    rows=app.session_state["demo_health_entries"]
    assert len(rows)==1 and rows[0]["id"]==identity
    assert rows[0]["details"]["nutrition"]["totals"]["kcal"]==295
