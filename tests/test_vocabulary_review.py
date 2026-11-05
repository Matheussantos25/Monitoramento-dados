from copy import deepcopy
import pytest
from streamlit.testing.v1 import AppTest
from solem_vocabulary import vocabulary_body, vocabulary_data, card_html
from solem_vocabulary_review import schedule_review, review_state

NOW=1793793600

def card():
    return dict(id='card-one',kind='note',title='notice',revision=1,archived=False,
                body=vocabulary_body(dict(word='notice',sentence="I couldn't help but notice.",
                    definition='To become aware of something.',image='https://upload.wikimedia.org/example.jpg')))

def test_steps_growth_lapses_and_no_early_regrading():
    assert [schedule_review(None,r,NOW)['due_at']-NOW for r in ('Errei','Difícil','Bom','Fácil')]==[60,300,600,345600]
    learning=schedule_review(None,'Bom',NOW)
    with pytest.raises(ValueError): schedule_review(learning,'Fácil',NOW)
    mature=schedule_review(learning,'Bom',NOW+600)
    assert mature['interval_days']==1 and mature['reviews']==2
    state=dict(mature,interval_days=10,due_at=NOW)
    assert [schedule_review(state,r,NOW)['interval_days'] for r in ('Difícil','Bom','Fácil')]==[12,25,33]
    failed=schedule_review(state,'Errei',NOW)
    assert failed['lapses']==1 and failed['interval_days']==0 and failed['due_at']==NOW+60
    assert state['interval_days']==10
    for _ in range(60):
        state=schedule_review(state,'Difícil',state['due_at'])
    assert state['ease_milli']==1300 and state['interval_days']<=36500

def test_legacy_and_content_edits_preserve_review_and_front_back():
    original=card(); data=vocabulary_data(original)
    assert 'review' not in data
    schedule=schedule_review(None,'Fácil',NOW)
    data['review']=schedule
    updated=dict(original,body=vocabulary_body(data))
    restored=vocabulary_data(updated)
    assert restored['review']==schedule
    restored['definition']='An edited meaning.'
    assert vocabulary_data(dict(updated,body=vocabulary_body(restored)))['review']==schedule
    front,back=card_html(data)
    assert '<b>notice</b>' in front and 'aware' not in front
    assert 'aware' in back and '<img ' in back and "couldn" not in back
    assert vocabulary_data(original).get('review') is None

def test_review_ui_requires_reveal_and_saves_once_without_new_activity(monkeypatch):
    monkeypatch.setattr('solem_vocabulary_review_ui.time.time',lambda: NOW)
    app=AppTest.from_string('from solem_vocabulary_ui import vocabulary_panel\nvocabulary_panel(demo=True)',default_timeout=30).run()
    item=card();item['body']=vocabulary_body(dict(vocabulary_data(item),image=''))
    app.session_state['demo_vocabulary_items']=[item]
    app.run()
    assert not any(x.label.startswith('Fácil ·') for x in app.button)
    next(x for x in app.button if x.label=='Mostrar resposta').click().run()
    next(x for x in app.button if x.label=='Fácil · 4 d').click().run()
    assert not app.exception
    records=deepcopy(app.session_state['demo_vocabulary_items'])
    assert len(records)==1 and records[0]['id']=='card-one'
    assert vocabulary_data(records[0])['review']['reviews']==1
    app.run()
    assert app.session_state['demo_vocabulary_items']==records
    assert not any(x.label=='Mostrar resposta' for x in app.button)
    app.selectbox(key='vocab_selected').set_value('card-one').run()
    next(x for x in app.text_area if x.label=='Significado em inglês').set_value('An updated definition.')
    next(x for x in app.button if x.label=='Salvar alterações da palavra').click().run()
    assert vocabulary_data(app.session_state['demo_vocabulary_items'][0])['review']==vocabulary_data(records[0])['review']
