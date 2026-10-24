from copy import deepcopy
from datetime import date
import pytest
from streamlit.testing.v1 import AppTest
from solem_meal_analysis import catalog
from solem_voice import parse_meal, parse_sleep, parse_weight, parse_workout


def test_full_cumulative_meal_and_individual_modes():
    foods = catalog(); original = deepcopy(foods)
    for text in ['Almoço arroz 170, feijão 323, ovo cozido 371, alface 386, purê 457, carne 491, peso acumulado',
                 'Peso acumulado da balança. Almoço, arroz cento e setenta, feijão trezentos e vinte e três, ovo cozido trezentos e setenta e um, alface 386, purê 457, carne 491']:
        result = parse_meal(text, foods)
        assert [i['grams'] for i in result['items']] == [170,153,48,15,71,34]
        assert result['cumulative'] and result['meal_type'] == 'Almoço'
    assert foods == original
    result = parse_meal('arroz 170, feijão 153, individual', foods)
    assert [i['grams'] for i in result['items']] == [170,153]
    assert not result['cumulative']
    assert parse_meal('Arroz 70,5 gramas, feijão 130,5 gramas', foods)['items'][1]['grams'] == 60


@pytest.mark.parametrize('text', [
    'arroz 170, feijão 160, acumulado', 'arroz 170, feijão 170',
    'arroz 170, comida desconhecida 200', 'arroz 170, frango',
    'arroz 170, individual e acumulado', 'arroz 2 kg',
    'almoço jantar arroz 170', 'arroz -10', 'arroz 170, feijão 4000',
    'arroz 170, feijão 323, ontem', 'arroz 170, prato 60', 'arroz 170 200',
])
def test_meal_rejects_partial_or_ambiguous_interpretation(text):
    with pytest.raises(ValueError): parse_meal(text, catalog())


def test_weight_sleep_and_workout():
    assert parse_weight('Peso sessenta e sete vírgula cinco quilos')['kg'] == 67.5
    assert parse_weight('67,5')['kg'] == 67.5
    assert parse_sleep('Dormi às três e acordei às treze e meia, na mesma data') == dict(kind='sleep',bed='03:00',wake='13:30',mode='same')
    assert parse_sleep('Dormi uma e quinze e acordei oito e quarenta e cinco')['bed'] == '01:15'
    assert parse_sleep('Dormi às vinte e três e trinta e acordei às sete, na noite anterior')['bed'] == '23:30'
    exercise = ['Agachamento','Flexão','Caminhada','Prancha']
    assert parse_workout('Agachamento, três séries de vinte, descanso de um minuto',exercise,'Flexão')['values'] == dict(series=3,repeticoes=60,descanso_seg=60)
    assert parse_workout('20 agachamentos',exercise,'Flexão')['exercise'] == 'Agachamento'
    assert parse_workout('Caminhada, 30 minutos, 2 vírgula 5 quilômetros',exercise,'Flexão')['values'] == dict(distancia_km=2.5,duracao_min=30)
    assert parse_workout('Prancha, 2 repetições, 30 segundos',exercise,'Flexão')['values'] == dict(repeticoes=2,isometria_segundos=30)
    for text in ['Dormi às 25 e acordei às 7','Dormi às 3 e acordei 13:70','Dormi ontem às 3 e acordei às 8']:
        with pytest.raises(ValueError): parse_sleep(text)
    for text in ['peso 700 kg','peso 67 libras','peso 67 e 68','-67']:
        with pytest.raises(ValueError): parse_weight(text)
    for text in ['Agachamento 20 e Flexão 30','agachamento 3 séries de 20 e 40 repetições','Caminhada 2 milhas']:
        with pytest.raises(ValueError): parse_workout(text,exercise,'Flexão')


MEAL_APP = '''
import streamlit as st
from datetime import date
from solem_meal_photo_ui import review_meal
def save(client,day,time,kind,details,message,old=None,demo=False):
    st.session_state.saves=st.session_state.get('saves',[])+[details]
review_meal(None,date(2026,10,24),{'items':[]},save,'voice_meal',demo=True,weighed=True)
'''


def test_voice_meal_review_does_not_save_until_confirmed_and_survives_reruns():
    app = AppTest.from_string(MEAL_APP).run()
    app.text_area(key='voice_meal_voice_text').set_value('Almoço arroz 170, feijão 323, ovo cozido 371, acumulado').run()
    assert 'saves' not in app.session_state
    app.button(key='voice_meal_voice_apply').click().run()
    assert not app.exception
    prefix='voice_meal_dictated_1_cum'
    assert app.number_input(key=prefix+'_reading_1').value == 323
    assert app.button(key=prefix+'_save').disabled
    assert 'saves' not in app.session_state
    app.number_input(key=prefix+'_reading_1').set_value(320).run()
    app.run()
    assert app.number_input(key=prefix+'_reading_1').value == 320
    app.checkbox(key=prefix+'_confirmed').check().run()
    app.button(key=prefix+'_save').click().run()
    assert not app.exception
    assert len(app.session_state.saves) == 1
    assert [i['grams'] for i in app.session_state.saves[0]['nutrition']['items']] == [170,150,51]
    app.run()
    assert len(app.session_state.saves) == 1


def test_voice_second_draft_replaces_first_without_stale_confirmation():
    app=AppTest.from_string(MEAL_APP).run()
    app.text_area(key='voice_meal_voice_text').set_value('arroz 170, feijão 323').run()
    app.button(key='voice_meal_voice_apply').click().run()
    app.checkbox(key='voice_meal_dictated_1_cum_confirmed').check().run()
    app.text_area(key='voice_meal_voice_text').set_value('Jantar frango 80, arroz 100, individual').run()
    app.button(key='voice_meal_voice_apply').click().run()
    assert not app.exception
    assert app.radio(key='voice_meal_dictated_2_weighing_mode').value == 'Peso individual de cada alimento'
    assert app.number_input(key='voice_meal_dictated_2_grams_0').value == 80
    assert app.selectbox(key='voice_meal_dictated_2_type').value == 'Jantar'
    assert app.button(key='voice_meal_dictated_2_save').disabled


def test_voice_training_and_health_prefill_never_save(monkeypatch):
    from pathlib import Path
    monkeypatch.setenv('SOLEM_DEMO','1')
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=40).run()
    app.radio(key='solem_page').set_value('Treino').run()
    app.text_area(key='workout_voice_text').set_value('Agachamento, 3 séries de 20, descanso de 60 segundos').run()
    app.button(key='workout_voice_apply').click().run()
    assert not app.exception
    assert app.selectbox(key='treino_exercicio').value == 'Agachamento'
    assert app.number_input(key='treino_repeticoes_Agachamento').value == 60
    app.radio(key='solem_page').set_value('Saúde').run()
    original_health=deepcopy(app.session_state['demo_health_entries'])
    day=app.date_input(key='health_day').value
    app.text_area(key=f'weight_voice_{day}_text').set_value('67 vírgula 5 quilos').run()
    app.button(key=f'weight_voice_{day}_apply').click().run()
    assert not app.exception
    assert app.number_input(key=f'weight_value_{day}').value == 67.5
    key=next(t.key for t in app.text_area if t.key.startswith('sleep_'))[:-5]
    app.text_area(key=key+'_text').set_value('Dormi às 3 e acordei às 13:30, na mesma data').run()
    app.button(key=key+'_apply').click().run()
    assert not app.exception
    assert next(t for t in app.text_input if t.label=='Horário em que dormiu').value == '03:00'
    assert app.session_state['demo_health_entries'] == original_health


def test_saving_resets_dictated_mode_and_does_not_reuse_old_readings():
    code='''
import streamlit as st
from datetime import date
from solem_meal_photo_ui import review_meal
from solem_health_ui import _save
review_meal(None,date(2026,10,24),{'items':[]},_save,'weighed_meal_2026-10-24',demo=True,weighed=True)
'''
    app=AppTest.from_string(code).run()
    key='weighed_meal_2026-10-24'
    app.text_area(key=key+'_voice_text').set_value('arroz 170, feijão 153, individual').run()
    app.button(key=key+'_voice_apply').click().run()
    app.checkbox(key=key+'_dictated_1_confirmed').check().run()
    app.button(key=key+'_dictated_1_save').click().run()
    assert not app.exception
    assert len(app.session_state['demo_health_entries']) == 1
    assert key+'_dictated_1_weighing_mode' not in app.session_state
    assert key+'_voice_proposal' not in app.session_state
    # A fresh frontend avoids AppTest retaining removed widget IDs across the
    # save-triggered rerun. Preserve the saved records and remaining form state.
    saved=deepcopy(app.session_state['demo_health_entries'])
    app=AppTest.from_string(code)
    app.session_state['demo_health_entries']=saved
    app.run()
    app.text_area(key=key+'_voice_text').set_value('Jantar arroz 100, feijão 200, acumulado').run()
    app.button(key=key+'_voice_apply').click().run()
    assert not app.exception
    assert app.radio(key=key+'_dictated_1_weighing_mode').value == 'Peso acumulado da balança'
    assert app.number_input(key=key+'_dictated_1_cum_reading_1').value == 200
    assert app.button(key=key+'_dictated_1_cum_save').disabled
    assert len(app.session_state['demo_health_entries']) == 1
