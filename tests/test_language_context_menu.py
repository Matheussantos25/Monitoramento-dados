from copy import deepcopy
from datetime import date
import os
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from solem_languages import language_session, media_titles, material_label
from solem_journey import preferences, JourneyStore
from solem_navigation import TABS, PINNED, menu_tabs, visible_menu


def test_listening_fields_are_saved_without_anki_counts_and_edit_clears_media_only():
    row = dict(id=1, **language_session(date(2026,11,3), "22:15", "Inglês", "Escuta", 25,
        title="Meu anime", episodes=1, audio="Inglês", subtitles="Sem legenda", reviewed=30,
        added=10, source="YouTube", content_type="Anime"))
    old = deepcopy(row)
    e = row['dados_extras']
    assert (e['cards_revisados'], e['cards_adicionados'], e['episodios']) == (0,0,1)
    assert e['fonte_idioma'] == 'YouTube' and e['tipo_conteudo'] == 'Anime'
    assert media_titles([row]) == ['Meu anime']
    changed = language_session(date(2026,11,3), "22:15", "Inglês", "Leitura",25, previous=row, source="Biblioteca")
    assert changed['dados_extras']['episodios'] == 0
    assert changed['dados_extras']['tipo_conteudo'] == ''
    assert changed['dados_extras']['fonte_idioma'] == 'Biblioteca'
    assert row == old
    assert 'baralho' not in material_label('Leitura').lower()


def test_menu_defaults_pin_recovery_and_preserve_preferences_and_other_accounts():
    old = preferences(personal=True)
    before = deepcopy(old)
    assert visible_menu(list(TABS.values()),old) == list(TABS.values())
    assert 'Financeiro' not in visible_menu(list(TABS.values()),preferences(generic=True),True)
    changed = preferences(dict(old, menu_tabs=['languages','finance','weight'],menu_done=True),personal=True)
    assert set(changed['menu_tabs']) == PINNED | {'languages','finance','weight'}
    assert changed['targets'] == old['targets'] and old == before
    assert 'Financeiro' in visible_menu(list(TABS.values()),changed,True)
    assert menu_tabs([]) == ['overview','settings','account']
    state={}
    a,b=JourneyStore(demo_state=state,demo_owner='a'),JourneyStore(demo_state=state,demo_owner='b')
    a.save_settings(changed)
    assert b.load()['settings'] is None
    assert a.load()['settings']['preferences']['menu_tabs']==changed['menu_tabs']


def test_save_listening_keeps_episode_context_and_does_not_duplicate_on_rerun():
    with patch.dict(os.environ,{'SOLEM_DEMO':'1','SOLEM_DEMO_PROFILE':'generic'}):
        app=AppTest.from_file('app.py',default_timeout=40).run()
        app.session_state['solem_demo_records'].append(dict(id=999, **language_session(
            date(2026,11,2),'21:00','Espanhol','Escuta',25,title='Minha série',episodes=1)))
        original=deepcopy(app.session_state['solem_demo_records'])
        app.radio(key='solem_page').set_value('Idiomas').run()
        app.selectbox(key='language_new_0_activity').set_value('Escuta').run()
        app.selectbox(key='language_new_0_language').set_value('Espanhol').run()
        assert not any('Cards' in x.label or 'baralho' in x.label for x in app.number_input)
        app.selectbox(key='language_new_0_Escuta_source').set_value('YouTube')
        app.selectbox(key='language_new_0_Escuta_content_type').set_value('Anime').run()
        app.selectbox(key='language_new_0_Escuta_media_title').set_value('Minha série')
        app.text_input(key='language_new_0_Escuta_audio').set_value('Japonês')
        assert not any(x.label=='Legendas' for x in app.selectbox)
        next(x for x in app.number_input if x.label=='Tempo efetivo da sessão (min)').set_value(45)
        next(x for x in app.number_input if x.label=='Conteúdos / episódios ouvidos').set_value(2)
        next(x for x in app.button if x.label=='Salvar sessão de idioma').click().run()
        assert not app.exception
        assert app.session_state['language_last_context']['titulo']=='Minha série'
        assert app.selectbox(key='language_new_1_activity').value=='Escuta'
        assert app.selectbox(key='language_new_1_language').value=='Espanhol'
        assert app.selectbox(key='language_new_1_Escuta_source').value=='YouTube'
        assert app.selectbox(key='language_new_1_Escuta_content_type').value=='Anime'
        assert app.selectbox(key='language_new_1_Escuta_media_title').value=='Minha série', app.session_state['language_last_context']
        assert app.text_input(key='language_new_1_Escuta_audio').value=='Japonês'
        assert not any(x.label=='Legendas' for x in app.selectbox)
        assert next(x for x in app.number_input if x.label=='Conteúdos / episódios ouvidos').value==1
        assert next(x for x in app.number_input if x.label=='Tempo efetivo da sessão (min)').value==20
        app.run()
        rows=app.session_state['solem_demo_records']
        assert rows[:-1]==original and len(rows)==len(original)+1
        assert rows[-1]['dados_extras']['fonte_idioma']=='YouTube'
        first=deepcopy(rows[-1])
        next(x for x in app.button if x.label=='Salvar sessão de idioma').click().run()
        assert not app.exception
        rows=app.session_state['solem_demo_records']
        assert len(rows)==len(original)+2 and rows[-2]==first
        assert rows[-1]['dados_extras']['titulo']=='Minha série'
        assert rows[-1]['dados_extras']['idioma_audio']=='Japonês'
        assert rows[-1]['dados_extras']['legendas']=='Sem legenda'
        assert rows[-1]['dados_extras']['episodios']==1


def test_choose_hide_restore_menu_without_changing_history():
    with patch.dict(os.environ,{'SOLEM_DEMO':'1','SOLEM_DEMO_PROFILE':'generic'}):
        app=AppTest.from_file('app.py',default_timeout=40).run()
        original=deepcopy(app.session_state['solem_demo_records'])
        app.multiselect(key='menu_welcome_tabs').set_value(['languages','finance'])
        next(x for x in app.button if x.label=='Começar com estas abas').click().run()
        assert not app.exception
        assert 'Financeiro' in app.radio(key='solem_page').options
        assert 'Treino' not in app.radio(key='solem_page').options
        assert 'Metas e aparência' in app.radio(key='solem_page').options
        app.radio(key='solem_page').set_value('Financeiro').run()
        assert not app.exception
        app.radio(key='solem_page').set_value('Metas e aparência').run()
        app.multiselect(key='menu_preferences_tabs').set_value(['languages','training'])
        next(x for x in app.button if x.label=='Salvar minhas abas').click().run()
        assert not app.exception
        assert 'Treino' in app.radio(key='solem_page').options
        assert 'Financeiro' not in app.radio(key='solem_page').options
        assert app.session_state['solem_demo_records']==original
