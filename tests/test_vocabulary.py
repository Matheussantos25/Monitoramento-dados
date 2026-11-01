import csv
import io
import json
import zipfile
from copy import deepcopy
import pytest
from streamlit.testing.v1 import AppTest
import solem_vocabulary as v


def example():
    return dict(word="run", sentence="Run, don't outrun me. I run.", definition="To move quickly on foot.", context="Episode 2", source="Dictionary", forms="", image="", image_page="", image_credit="")


def test_round_trip_private_note_and_legacy():
    value=example(); item=dict(kind="note",body=v.vocabulary_body(value))
    assert v.vocabulary_data(item)==value
    assert v.vocabulary_data(dict(kind="note",body="legacy note")) is None
    assert v.vocabulary_data(dict(kind="note",body=v.PREFIX+'[]')) is None
    assert v.vocabulary_data(dict(kind="note",body=v.PREFIX+'{"word":5}')) is None
    with pytest.raises(ValueError): v.vocabulary_body(dict(word=""))


def test_html_word_boundaries_and_injection():
    value=example(); front,back=v.card_html(value)
    assert front.count('<b>')==2 and 'out<b>' not in front
    value.update(word="a+b",sentence='Use a+b <script>evil()</script>',definition='<img src=x onerror="evil()">')
    front,back=v.card_html(value)
    assert '<b>a+b</b>' in front and '<script>' not in front and '<img src=x' not in back
    with pytest.raises(ValueError): v.card_html(dict(value,sentence="missing"))
    assert not v.media_url('https://upload.wikimedia.org.evil.com/a.jpg')
    assert not v.media_url('https://user@upload.wikimedia.org/a.jpg')
    assert not v.media_url('http://upload.wikimedia.org/a.jpg')


def test_export_preserves_fields_and_embeds_local_media(monkeypatch):
    value=example();value.update(image='https://upload.wikimedia.org/a.jpg',image_credit='Artist · CC BY 4.0',definition='A "definition"\twith a tab\nand line')
    monkeypatch.setattr(v,'fetch',lambda *a:(b'\xff\xd8sample','image/jpeg'))
    with zipfile.ZipFile(io.BytesIO(v.anki_package(value))) as archive:
        text=archive.read('card.txt').decode()
        fields=list(csv.reader(io.StringIO('\n'.join(text.splitlines()[3:])),delimiter='\t'))
        assert len(fields)==1 and len(fields[0])==2
        assert 'Artist' in fields[0][1]
        assert 'https://upload.wikimedia.org' not in fields[0][1]
        media=[n for n in archive.namelist() if n.startswith('media/')]
        assert len(media)==1 and media[0].split('/')[1] in fields[0][1]
        assert '\twith a tab<br>and line' in fields[0][1]


def test_dictionary_does_not_fabricate_example_and_filters_language(monkeypatch):
    payload={'entries':[{'language':{'code':'en'},'partOfSpeech':'noun','senses':[{'definition':'A fruit.'},{'definition':'A computer.','examples':['Use this apple.']}]},{'language':{'code':'es'},'senses':[{'definition':'wrong'}]}]}
    calls=[]
    monkeypatch.setattr(v,'fetch',lambda url:(calls.append(url) or json.dumps(payload).encode(),'application/json'))
    senses=v.dictionary('apple')
    assert len(senses)==2 and senses[0]['sentence']=='' and senses[1]['sentence']=='Use this apple.'
    assert 'Wiktionary' in senses[0]['source']
    assert len(calls)==1


def test_capture_edit_trash_restore_no_activity_records():
    app=AppTest.from_string('from solem_vocabulary_ui import vocabulary_panel\nvocabulary_panel(demo=True)',default_timeout=40).run()
    assert not app.exception
    next(x for x in app.text_input if x.label=='Palavra ou expressão em inglês').set_value('run')
    next(b for b in app.button if b.label=='Salvar palavra').click().run()
    assert not app.exception
    items=app.session_state['demo_vocabulary_items'];assert len(items)==1
    identity=items[0]['id']
    next(x for x in app.text_area if x.label.startswith('Frase em')).set_value('I run every morning.')
    next(x for x in app.text_area if x.label=='Significado em inglês').set_value('To move quickly on foot.')
    next(b for b in app.button if b.label=='Salvar alterações da palavra').click().run()
    assert not app.exception and len(items)==1 and items[0]['id']==identity
    assert app.get('iframe')
    original=deepcopy(items[0])
    next(b for b in app.button if b.label=='Mover palavra para a lixeira').click().run()
    assert items[0]['archived']
    app.toggle(key='vocab_trash').set_value(True).run()
    app.selectbox(key='vocab_selected').set_value(identity).run()
    next(b for b in app.button if b.label=='Restaurar palavra').click().run()
    assert not items[0]['archived'] and items[0]['body']==original['body']


def test_lookup_failure_keeps_draft(monkeypatch):
    import solem_vocabulary_ui as ui
    monkeypatch.setattr(ui,'lookup',lambda word: (_ for _ in ()).throw(OSError('unavailable')))
    app=AppTest.from_string('from solem_vocabulary_ui import vocabulary_panel\nvocabulary_panel(demo=True)',default_timeout=40).run()
    next(x for x in app.text_input if x.label=='Palavra ou expressão em inglês').set_value('stumble').run()
    next(x for x in app.text_area if x.label.startswith('Frase em')).set_value('Do not stumble.')
    next(b for b in app.button if b.label=='Buscar significado e exemplo').click().run()
    assert not app.exception and app.warning
    assert next(x for x in app.text_area if x.label.startswith('Frase em')).value=='Do not stumble.'
    assert app.session_state['demo_vocabulary_items']==[]


def test_dictionary_inflections_are_bolded():
    value=example();value.update(word="run",sentence="She ran home.",forms="runs\nran\nrunning")
    assert "<b>ran</b>" in v.card_html(value)[0]
