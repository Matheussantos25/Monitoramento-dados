from copy import deepcopy
from datetime import date
from streamlit.testing.v1 import AppTest
from solem_meal_analysis import meal_details, overview_nutrition

DAY = date(2026, 10, 27)


def meal(id, grams=44, day=DAY):
    return dict(id=id, day=str(day), kind="meal", details=meal_details("Café da manhã",
        [dict(name="Pão com manteiga",food_id="tbca-BRC0418A",grams=grams)], True))


def test_daily_total_updates_on_add_edit_delete_and_excludes_other_days_and_kinds():
    rows=[meal("a"),meal("b"),meal("yesterday",day=date(2026,10,26)),
          dict(day=str(DAY),kind="weight",details={"kg":68}),
          dict(day=str(DAY),kind="meal",details={"sem_refeicao":True})]
    before=deepcopy(rows)
    result=overview_nutrition(rows,DAY)
    assert result["totals"]["kcal"]==374.8 and result["totals"]["protein_g"]==6.4
    assert result["meals"]==2 and not result["partial"]
    assert rows==before
    rows[1]=meal("b",100)
    assert overview_nutrition(rows,DAY)["totals"]["kcal"]==613.4
    rows.pop(1)
    assert overview_nutrition(rows,DAY)["totals"]["kcal"]==187.4
    assert overview_nutrition([],DAY)["meals"]==0
    assert overview_nutrition(None,DAY) is None


def test_partial_unknown_and_invalid_meals_are_not_shown_as_complete_zero():
    rows=[meal("a"),dict(day=str(DAY),kind="meal",details={}),
          dict(day=str(DAY),kind="meal",details={"nutrition":{"items":"invalid"}})]
    result=overview_nutrition(rows,DAY)
    assert result["partial"] and result["known_items"]==1 and result["meals"]==3
    assert result["totals"]["kcal"]==187.4
    rows=[dict(day=str(DAY),kind="meal",details=meal_details("Lanche",
        [dict(name="Alimento sem referência",food_id="",grams=10)]))]
    assert overview_nutrition(rows,DAY)["known_items"]==0


def test_highlight_distinguishes_loaded_empty_partial_and_unavailable():
    app=AppTest.from_string('''
from datetime import date
import streamlit as st
from solem_nutrition_overview_ui import nutrition_highlight
nutrition_highlight(st.session_state.entries,date(2026,10,27))
''')
    for entries,text in [(None,"Diário indisponível"),([],"Nenhuma refeição"),
                         ([meal("a")],"187,4"),([dict(day=str(DAY),kind="meal",details={})],"Sem cálculo ainda")]:
        app.session_state.entries=entries
        app.run()
        assert not app.exception
        assert text in app.get("html")[0].proto.body
