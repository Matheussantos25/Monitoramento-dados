from copy import deepcopy
import pytest
from streamlit.testing.v1 import AppTest
from solem_scripts import script_body, script_data
from solem_workspace import validate_item

def test_versioned_documents_preserve_text_and_legacy():
    text='Olá\n</script><script>alert(1)</script> 😀 "aspas"'
    item=dict(kind="note",title="Título",body=script_body("script",text,"Descrição","gacha, vídeo"))
    validate_item(item)
    assert script_data(item)["text"]==text
    assert script_data(dict(kind="note",body="anotação normal")) is None
    assert script_data(dict(kind="note",body='SOLEM_SCRIPT_V1\n[]')) is None
    with pytest.raises(ValueError): script_body("script","a"*40001,"","")

def test_create_edit_trash_restore_and_teleprompter():
    app=AppTest.from_string('from solem_scripts_ui import scripts_page\nscripts_page(demo=True)',default_timeout=40).run()
    assert not app.exception
    next(x for x in app.text_input if x.label=="Título").set_value("Ideia para vídeo")
    next(x for x in app.text_area if x.label=="Ideia / texto do roteiro").set_value("Primeira frase.\nSegunda frase.")
    next(x for x in app.selectbox if x.label=="Tipo").set_value("Roteiro")
    next(b for b in app.button if b.label=="Salvar documento").click().run()
    assert not app.exception
    saved=app.session_state["demo_script_items"]
    assert len(saved)==1
    identity=saved[0]["id"]
    app.selectbox(key="script_selected").set_value(identity).run()
    assert app.get("component_instance")
    next(x for x in app.text_area if x.label=="Ideia / texto do roteiro").set_value("Texto revisado")
    next(b for b in app.button if b.label=="Salvar documento").click().run()
    assert len(saved)==1 and script_data(saved[0])["text"]=="Texto revisado"
    original=deepcopy(saved[0])
    next(b for b in app.button if b.label=="Mover documento para a lixeira").click().run()
    assert saved[0]["archived"]
    app.toggle(key="script_trash").set_value(True).run()
    app.selectbox(key="script_selected").set_value(identity).run()
    next(b for b in app.button if b.label=="Restaurar documento").click().run()
    assert not saved[0]["archived"] and saved[0]["body"]==original["body"]
