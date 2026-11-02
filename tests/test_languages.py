import os
from copy import deepcopy
from datetime import date
from unittest.mock import patch
import pytest
from streamlit.testing.v1 import AppTest
from solem_languages import *
from solem_progress import calculate_progress

DAY=date(2026,11,1)

def session(**kwargs):
    return language_session(DAY,"10:30","Inglês","Revisão no Anki",20,**kwargs)

def test_counts_time_once_and_never_counts_cards_as_questions():
    anki=dict(id=1,**session(reviewed=40,added=5))
    media=dict(id=2,**language_session(DAY,"11:30","Inglês","Série / vídeo",50,title="Minha série",episodes=2,audio="Inglês",subtitles="Sem legenda"))
    spanish=dict(id=3,**language_session(DAY,"12:30","Espanhol","Leitura",15))
    original=deepcopy([anki,media,spanish])
    totals=language_summary(original+[anki],DAY,"Inglês")
    assert totals==dict(minutes=70,review_minutes=20,reviewed=40,added=5,episodes=2,sessions=2)
    assert language_summary(original,DAY)["minutes"]==85
    progress=calculate_progress(original,DAY)
    assert progress["questions"]==0 and progress["study_minutes"]==85 and progress["xp"]==30
    assert original==[anki,media,spanish]
    assert len(language_week(original,DAY))==7

def test_switching_activity_clears_incompatible_metrics_and_preserves_unrelated_metadata():
    old=dict(dados_extras=dict(language_schema=1,cards_revisados=20,episodios=2,tempo_segundos_exato=80,custom="preserved"))
    updated=language_session(DAY,"10:00","Espanhol","Leitura",30,reviewed=40,added=50,episodes=2,previous=old)
    e=updated['dados_extras']
    assert e['cards_revisados']==e['cards_adicionados']==e['episodios']==0
    assert 'tempo_segundos_exato' not in e and e['custom']=='preserved'
    assert old['dados_extras']['tempo_segundos_exato']==80

@pytest.mark.parametrize('kwargs',[dict(reviewed=-1),dict(added=1.2),dict(notes='a'*2001)])
def test_invalid_counts_and_lengths(kwargs):
    with pytest.raises(ValueError): session(**kwargs)

def test_incomplete_media_and_empty_duration_rejected():
    with pytest.raises(ValueError): language_session(DAY,"10:00","Inglês","Série / vídeo",40)
    with pytest.raises(ValueError): language_session(DAY,"10:00","Inglês","Leitura",0)

def test_new_account_create_edit_without_duplicate_and_keep_existing_history():
    with patch.dict(os.environ,{"SOLEM_DEMO":"1","SOLEM_DEMO_PROFILE":"generic"}):
        app=AppTest.from_file("app.py",default_timeout=40).run()
        assert not app.exception
        initial=deepcopy(app.session_state['solem_demo_records'])
        app.radio(key='solem_page').set_value('Idiomas').run()
        assert not app.exception
        next(x for x in app.number_input if x.label=='Cards revisados').set_value(35)
        next(x for x in app.number_input if x.label=='Cards adicionados ao Anki').set_value(7)
        next(x for x in app.button if x.label=='Salvar sessão de idioma').click().run()
        assert not app.exception
        rows=app.session_state['solem_demo_records']
        assert len(rows)==len(initial)+1
        row=rows[-1]; assert row['dados_extras']['cards_adicionados']==7
        # Expanded or collapsed, editing the existing form must UPDATE its ID.
        [x for x in app.number_input if x.label=='Tempo efetivo da sessão (min)'][1].set_value(30)
        next(x for x in app.button if x.label=='Salvar alterações').click().run()
        assert not app.exception
        app.run()
        rows=app.session_state['solem_demo_records']
        assert len(rows)==len(initial)+1 and rows[-1]['id']==row['id'] and rows[-1]['duracao_min']==30
        assert rows[:-1]==initial
        assert next(m for m in app.metric if m.label=='Tempo de estudo').value=='30 min'

        app.selectbox(key='language_new_2_activity').set_value('Série / vídeo').run()
        title_input=next(x for x in app.selectbox if x.label=='Série, anime, filme ou vídeo')
        # AppTest 1.59 does not serialize accept_new_options; emulate the frontend's new string option.
        title_input.options.append('Série de teste')
        title_input.set_value('Série de teste')
        [x for x in app.number_input if x.label=='Tempo efetivo da sessão (min)'][0].set_value(50)
        next(x for x in app.number_input if x.label=='Episódios / vídeos vistos').set_value(2)
        next(x for x in app.selectbox if x.label=='Legendas').set_value('Sem legenda')
        next(x for x in app.button if x.label=='Salvar sessão de idioma').click().run()
        assert not app.exception
        rows=app.session_state['solem_demo_records']
        assert len(rows)==len(initial)+2
        assert rows[-1]['dados_extras']['episodios']==2 and rows[-1]['dados_extras']['legendas']=='Sem legenda'
        assert next(m for m in app.metric if m.label=='Tempo de estudo').value=='80 min'
