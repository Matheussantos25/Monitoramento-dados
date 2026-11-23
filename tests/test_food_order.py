from copy import deepcopy
from streamlit.testing.v1 import AppTest
from solem_food_order import apply_order_event, sync_order
from solem_meal_analysis import meal_details


def test_stale_or_invalid_events_cannot_change_foods_or_readings():
    state = {}
    sync_order(state, "x", ["a", "b", "c"], {"a": 69, "b": 128, "c": 201})
    initial = deepcopy(state)
    for proposed, rev in [(["a", "a", "c"], 1), (["a", "c"], 1), (["c", "b", "a"], 0), (["a", "b", "other"], 1)]:
        assert not apply_order_event(state, "x", dict(base=["a", "b", "c"], order=proposed, revision=rev))
        assert state == initial
    assert apply_order_event(state, "x", dict(base=["a", "b", "c"], order=["b", "c", "a"], revision=1))
    assert [state[f"x_slot_reading_{i}"] for i in range(3)] == [69, 128, 201]
    assert sync_order(state, "x", ["a", "b", "c", "d"], {}) == ["b", "c", "a", "d"]
    assert state["x_slot_reading_3"] == 0
    assert sync_order(state, "x", ["a", "b", "d"], {}) == ["b", "a", "d"]
    assert [state[f"x_slot_reading_{i}"] for i in range(3)] == [69, 0, 0]


def test_reorder_edit_preserves_readings_time_id_and_requires_confirmation():
    original = dict(id="existing",logged_at="13:23:00",details=meal_details("Almoço",[
        dict(name="Arroz",food_id="169757",grams=69),
        dict(name="Feijão",food_id="175200",grams=59)],True,
        dict(baseline_g=0,readings_g=[69,128])))
    app=AppTest.from_string('''
import streamlit as st
from datetime import date
from solem_cumulative_meal_ui import cumulative_review
from solem_food_order import apply_order_event
def move():
    apply_order_event(st.session_state,"edit",dict(base=st.session_state.edit_order,
        order=list(reversed(st.session_state.edit_order)),revision=st.session_state.edit_order_revision))
st.button("Move",key="move",on_click=move)
def save(client,day,time,kind,details,message,old=None,demo=False):
    st.session_state.saved=dict(id=old["id"],logged_at=time,details=details)
    st.session_state.old=st.session_state.saved
old=st.session_state.old
cumulative_review(None,date(2026,11,23),old["details"]["nutrition"],save,"edit",old=old)
''',default_timeout=40)
    app.session_state.old=deepcopy(original)
    app.run()
    app.checkbox(key="edit_confirmed").check().run()
    app.button(key="move").click().run()
    assert not app.exception
    assert not app.checkbox(key="edit_confirmed").value
    assert app.button(key="edit_save").disabled
    assert app.session_state.old == original
    assert [app.number_input(key=f"edit_slot_reading_{i}").value for i in range(2)] == [69,128]
    assert "Feijão" in app.number_input(key="edit_slot_reading_0").label
    app.checkbox(key="edit_confirmed").check().run()
    app.button(key="edit_save").click().run()
    saved=app.session_state.saved
    assert (saved["id"],saved["logged_at"]) == ("existing","13:23:00")
    assert [(i["name"],i["grams"]) for i in saved["details"]["nutrition"]["items"]] == [("Feijão",69),("Arroz",59)]
    app.run()
    assert "Feijão" in app.number_input(key="edit_slot_reading_0").label
    assert app.session_state.edit_order == ["source:0","source:1"]
    assert not app.checkbox(key="edit_confirmed").value
