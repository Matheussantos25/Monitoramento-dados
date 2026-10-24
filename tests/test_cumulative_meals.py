from copy import deepcopy
import pytest
from streamlit.testing.v1 import AppTest
from solem_meal_analysis import cumulative_items,meal_details,day_nutrition

ITEMS=[dict(name="Feijão",food_id="175200",grams=0),dict(name="Arroz",food_id="169757",grams=0),dict(name="Outro",food_id="",grams=0)]

def test_opening_legacy_editor_keeps_individual_weights_without_saving():
    old=dict(id="legacy",logged_at="13:30:00",details=meal_details("Almoço",[
        dict(name="Feijão",food_id="175200",grams=69),
        dict(name="Arroz",food_id="169757",grams=128)],True))
    original=deepcopy(old)
    app=AppTest.from_string('''
import streamlit as st
from datetime import date
from solem_meal_photo_ui import review_meal
def save(*args, **kwargs):
    raise AssertionError("Opening a form must not save")
old=st.session_state.old
review_meal(None,date(2026,10,23),old["details"]["nutrition"],save,"legacy",old=old)
''',default_timeout=40)
    app.session_state.old=old
    app.run()
    assert not app.exception
    assert app.radio(key="legacy_weighing_mode").value=="Peso individual de cada alimento"
    assert app.number_input(key="legacy_grams_1").value==128
    assert app.session_state.old==original


@pytest.mark.parametrize("baseline,readings,expected",[
    (0,[60,128,201],[60,68,73]),(0,[69,128,201],[69,59,73]),
    (250,[310,378,451],[60,68,73]),(0,[60.5,128.5,201.7],[60.5,68,73.2]),
    (0,[60,60,201],[60,0,141])])
def test_differences_order_tare_and_decimals(baseline,readings,expected):
    original=deepcopy(ITEMS)
    assert [x["grams"] for x in cumulative_items(ITEMS,baseline,readings)]==expected
    assert ITEMS==original

@pytest.mark.parametrize("baseline,readings",[
    (-1,[60,128,201]),(10001,[60,128,201]),(float("nan"),[60,128,201]),
    (0,[60,50,201]),(100,[60,128,201]),(0,[60,128]),(0,[60,128,float("inf")]),
    (0,[60,128,2200]),(0,[True,128,201]),(0,[60,"128",201])])
def test_invalid_readings_never_produce_a_meal(baseline,readings):
    with pytest.raises(ValueError): meal_details("Almoço",ITEMS,True,dict(baseline_g=baseline,readings_g=readings))

def test_payload_and_daily_math_use_differences_not_scale_totals():
    details=meal_details("Almoço",ITEMS,True,dict(baseline_g=250,readings_g=[310,378,451]))
    assert details["weighing"]["readings_g"]==[310,378,451]
    assert [x["grams"] for x in details["nutrition"]["items"]]==[60,68,73]
    result=day_nutrition([dict(details=details)])
    assert result["totals"]["kcal"]==174.2 and result["partial"]
    assert meal_details("Almoço",[dict(name="Arroz",food_id="169757",grams=68)],True)["nutrition"]["totals"]["kcal"]==88.4

def test_cumulative_create_edit_and_reject_decreasing_reading():
    code='''
import streamlit as st
from datetime import date
from solem_meal_photo_ui import review_meal
def save(client,day,time,kind,details,message,old=None,demo=False):
    st.session_state.saved=details
old=st.session_state.get("old")
review_meal(None,date(2026,10,23),old["details"]["nutrition"] if old else {"items":[]},save,"scale",old=old,demo=True,weighed=True)
'''
    app=AppTest.from_string(code,default_timeout=40).run()
    assert app.radio(key="scale_weighing_mode").value=="Peso acumulado da balança"
    app.multiselect(key="scale_cum_added").set_value(["175200","169757"]).run()
    app.number_input(key="scale_cum_baseline").set_value(250)
    app.number_input(key="scale_cum_reading_extra_175200").set_value(310)
    app.number_input(key="scale_cum_reading_extra_175200_169757").set_value(378).run()
    app.checkbox(key="scale_cum_confirmed").check().run()
    app.button(key="scale_cum_save").click().run()
    assert not app.exception
    details=app.session_state.saved
    assert [x["grams"] for x in details["nutrition"]["items"]]==[60,68]
    app.number_input(key="scale_cum_reading_extra_175200_169757").set_value(300).run()
    assert app.button(key="scale_cum_save").disabled
    # New editor restores the original readings rather than treating grams as totals.
    edit=AppTest.from_string(code,default_timeout=40)
    edit.session_state["old"]=dict(id="a",logged_at="12:00:00",details=details)
    edit.run()
    assert edit.radio(key="scale_weighing_mode").value=="Peso acumulado da balança"
    assert edit.number_input(key="scale_cum_reading_1").value==378
    edit.number_input(key="scale_cum_reading_0").set_value(319).run()
    edit.checkbox(key="scale_cum_confirmed").check().run()
    edit.button(key="scale_cum_save").click().run()
    assert [x["grams"] for x in edit.session_state.saved["nutrition"]["items"]]==[69,59]
    assert details["weighing"]["readings_g"]==[310,378]

def test_diary_stores_and_edits_one_cumulative_record(monkeypatch):
    from pathlib import Path
    monkeypatch.setenv("SOLEM_DEMO","1")
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=40).run()
    app.radio(key="solem_page").set_value("Saúde").run()
    day=app.date_input(key="health_day").value
    key=f"weighed_meal_{day}"
    assert app.radio(key=f"{key}_weighing_mode").value=="Peso acumulado da balança"
    app.multiselect(key=f"{key}_cum_added").set_value(["175200","169757","168928"]).run()
    app.number_input(key=f"{key}_cum_reading_extra_175200").set_value(60)
    app.number_input(key=f"{key}_cum_reading_extra_175200_169757").set_value(128)
    app.number_input(key=f"{key}_cum_reading_extra_175200_169757_168928").set_value(201).run()
    app.checkbox(key=f"{key}_cum_confirmed").check().run()
    app.button(key=f"{key}_cum_save").click().run()
    assert not app.exception
    rows=app.session_state["demo_health_entries"]
    assert len(rows)==1
    assert app.radio(key=f"{key}_weighing_mode").value=="Peso acumulado da balança"
    row=rows[0]; edit=f"meal_nutrition_{row['id']}_cum"
    assert [x["grams"] for x in row["details"]["nutrition"]["items"]]==[60,68,73]
    assert app.number_input(key=f"{edit}_reading_0").value==60
    app.number_input(key=f"{edit}_reading_0").set_value(69).run()
    app.checkbox(key=f"{edit}_confirmed").check().run()
    app.button(key=f"{edit}_save").click().run()
    assert not app.exception
    rows=app.session_state["demo_health_entries"]
    assert len(rows)==1
    assert rows[0]["id"]==row["id"]
    assert [x["grams"] for x in rows[0]["details"]["nutrition"]["items"]]==[69,59,73]
