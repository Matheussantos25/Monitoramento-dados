from datetime import datetime, time
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


def test_water_reset_default_and_saved_time_are_local_not_server_utc():
    app=AppTest.from_string('from solem_health_ui import health_page\nhealth_page(None, [], [], demo=True)',default_timeout=30)
    with patch('solem_health_ui.now_local',return_value=datetime(2026,11,4,11,20)):
        app.run()
        widget=app.time_input(key='water_new_time_2026-11-04')
        assert widget.value==time(11,20)
        assert widget.proto.default=='11:20'  # The browser's clear_on_submit reset value.
        next(x for x in app.button if x.label=='Adicionar água').click().run()
        assert not app.exception
        assert app.session_state['demo_health_entries'][0]['logged_at']=='11:20:00'
        assert app.time_input(key='water_new_time_2026-11-04').proto.default=='11:20'
        app.time_input(key='water_new_time_2026-11-04').set_value(time(9,35))
        next(x for x in app.button if x.label=='Adicionar água').click().run()
        assert app.session_state['demo_health_entries'][-1]['logged_at']=='09:35:00'


def test_meal_keeps_selected_time_when_clock_changes_before_submit():
    app=AppTest.from_string('''
from solem_health_ui import health_page
health_page(None, ["Banana"], [], demo=True)
''',default_timeout=30)
    with patch('solem_health_ui.now_local',return_value=datetime(2026,11,1,10,45)):
        app.run()
        app.time_input(key='simple_meal_time_2026-11-01').set_value(time(10,30))
        next(x for x in app.text_input if x.label=='Outro alimento habitual').set_value('Amendoim — 17 g')
    with patch('solem_health_ui.now_local',return_value=datetime(2026,11,1,10,47)):
        next(x for x in app.button if x.label=='Salvar refeição').click().run()
    assert not app.exception
    rows=app.session_state['demo_health_entries']
    assert len(rows)==1
    assert rows[0]['logged_at']=='10:30:00'
    assert rows[0]['details']['saudaveis']==['Amendoim — 17 g']
