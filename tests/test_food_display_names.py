from copy import deepcopy
from datetime import date

from streamlit.testing.v1 import AppTest
from solem_meal_analysis import catalog, food_display_name, meal_details, nutrition


def test_display_names_are_unique_and_keep_custom_names():
    foods = catalog()
    assert len({food["display_name"] for food in foods}) == len(foods)
    assert food_display_name(foods[0]["name"]) == "Arroz"
    assert food_display_name("Feijão tipo pinto, grãos cozidos sem caldo") == "Feijão"
    assert food_display_name("Carne bovina moída, 10% gordura, cozida") == "Carne"
    assert food_display_name("Purê de batata com leite") == "Purê de batata"
    assert food_display_name("Arroz da minha receita") == "Arroz da minha receita"


def test_displaying_saved_meal_preserves_payload_and_nutrition():
    foods = {food["id"]: food for food in catalog()}
    readings = [170, 323, 371, 386, 457, 491]
    ids = ["169757", "175200", "173424", "169249", "170493", "171793"]
    items = [dict(name=foods[id]["name"], food_id=id, grams=0) for id in ids]
    saved = meal_details("Almoço", items, True, dict(baseline_g=0, readings_g=readings))
    before = deepcopy(saved)
    assert [food_display_name(item["name"]) for item in saved["nutrition"]["items"]] == [
        "Arroz", "Feijão", "Ovo cozido", "Alface", "Purê de batata", "Carne"]
    assert saved == before
    assert saved["nutrition"]["totals"]["kcal"] == 644.7
    assert saved["nutrition"]["totals"]["protein_g"] == 34.5
    assert nutrition(saved["nutrition"]["items"]) == before["nutrition"]


def test_legacy_editor_displays_alias_but_saves_unchanged_name_and_reference():
    original = meal_details("Almoço", [dict(name=catalog()[0]["name"], food_id="169757", grams=170)], True)
    code = '''
import streamlit as st
from datetime import date
from solem_meal_photo_ui import review_meal
def save(*args, **kwargs):
    st.session_state.saved=args[4]
old=st.session_state.old
review_meal(None,date(2026,10,24),old["details"]["nutrition"],save,"edit",old=old)
'''
    app = AppTest.from_string(code, default_timeout=40)
    app.session_state.old = dict(id="old", logged_at="14:52:00", details=deepcopy(original))
    app.run()
    assert not app.exception
    assert app.text_input(key="edit_name_0").value == "Arroz"
    assert app.selectbox(key="edit_food_0").value == "169757"
    assert "Purê de batata com manteiga" in app.selectbox(key="edit_food_0").options
    assert app.session_state.old["details"] == original
    app.checkbox(key="edit_confirmed").check().run()
    app.button(key="edit_save").click().run()
    assert not app.exception
    assert app.session_state.saved == original


def test_cumulative_new_meal_uses_short_labels_and_original_ids():
    code = '''
from datetime import date
from solem_meal_photo_ui import review_meal
review_meal(None,date(2026,10,24),{"items":[]},lambda *a,**k:None,"new")
'''
    app = AppTest.from_string(code, default_timeout=40).run()
    app.multiselect(key="new_cum_added").set_value(["169757", "170493"]).run()
    assert not app.exception
    assert app.number_input(key="new_cum_reading_extra_169757").label == "1. Balança após Arroz (g)"
    assert app.number_input(key="new_cum_reading_extra_169757_170493").label == "2. Balança após Purê de batata (g)"
