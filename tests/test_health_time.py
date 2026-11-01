from datetime import datetime, time
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


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
