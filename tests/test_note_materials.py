import json
import pytest
from io import BytesIO
from PIL import Image
from streamlit.testing.v1 import AppTest
from solem_note_materials import PREFIX, compact_image, folder_images, material
from solem_workspace import validate_item

FOLDER = "a5a56cce-677c-4f7e-98de-969a8e253a26"

def test_image_fits_private_item_limit():
    buffer = BytesIO()
    Image.effect_noise((1600, 1000), 80).convert("RGB").save(buffer, "PNG")
    buffer.seek(0)
    data = dict(folder=FOLDER, type="image", value=compact_image(buffer))
    row = dict(title="Foto", kind="note", body=PREFIX + json.dumps(data))
    validate_item(row)
    assert material(row) == data

def test_folder_link_roundtrip_and_trash():
    app = AppTest.from_string("""
import streamlit as st
from solem_workspace_ui import render_workspace
class Repo:
    def save(self, item, new_id=None):
        st.session_state.rows.append(dict(item,id=new_id,revision=1,archived=False))
    def archive(self,item,archived):
        item['archived']=archived
rows=st.session_state.setdefault("rows",[dict(id="a5a56cce-677c-4f7e-98de-969a8e253a26",title="Pasta A",kind="note",body="Texto original",revision=1,archived=False)])
render_workspace(Repo(),rows,"Anotações")
""", default_timeout=30).run()
    app.radio(key="ws_select_note_False").set_value(FOLDER).run()
    next(x for x in app.radio if x.label=="Adicionar à pasta").set_value("Link").run()
    next(x for x in app.text_input if x.label=="Título do material").set_value("Fonte")
    next(x for x in app.text_input if x.label=="Endereço do link").set_value("https://example.org")
    next(x for x in app.button if x.label=="Adicionar material").click().run()
    assert not app.exception and len(app.session_state.rows)==2
    assert app.get("link_button")[0].proto.url=="https://example.org"
    next(x for x in app.button if x.label=="Mover material para a lixeira").click().run()
    assert app.session_state.rows[1]["archived"]
    next(x for x in app.toggle if x.label=="Lixeira desta pasta").set_value(True).run()
    next(x for x in app.button if x.label=="Restaurar material").click().run()
    assert not app.exception and not app.session_state.rows[1]["archived"]
    assert app.session_state.rows[0]["body"]=="Texto original"

def test_multiple_images_keep_independent_ids_titles_and_folder_on_retry():
    uploads = []
    for name, color in [("mesa.png", "blue"), ("livro.jpg", "red")]:
        image = BytesIO()
        Image.new("RGB", (24, 16), color).save(image, "PNG")
        image.name = name
        uploads.append(image)
    rows = folder_images(uploads, FOLDER, FOLDER)
    assert [row["title"] for row in rows] == ["mesa", "livro"]
    assert len({row["id"] for row in rows}) == 2
    assert all(material(row)["folder"] == FOLDER for row in rows)
    assert folder_images(uploads, FOLDER, FOLDER) == rows
    named = folder_images(uploads, FOLDER, FOLDER, "Aula")
    assert [row["title"] for row in named] == ["Aula · 1", "Aula · 2"]
    bad = BytesIO(b"invalid")
    bad.name = "ilegivel.jpg"
    with pytest.raises(ValueError, match="ilegivel.jpg"):
        folder_images([uploads[0], bad], FOLDER, FOLDER)

def test_folder_form_submits_two_images_together():
    app = AppTest.from_string("""
import streamlit as st
from solem_note_materials import folder_panel, material
class Repo:
    def add_folder_images(self, rows):
        st.session_state.rows.extend(dict(row, archived=False) for row in rows)
rows = st.session_state.setdefault("rows", [])
folder_panel(Repo(), {"id": "a5a56cce-677c-4f7e-98de-969a8e253a26"}, [(r, material(r)) for r in rows])
""", default_timeout=30).run()
    image = BytesIO()
    Image.new("RGB", (20, 20)).save(image, "PNG")
    assert app.file_uploader[0].accept_multiple_files
    app.file_uploader[0].set_value([(name, image.getvalue(), "image/png") for name in ("capa.png", "mapa.png")])
    next(b for b in app.button if b.label == "Adicionar imagens à pasta").click().run()
    assert not app.exception
    assert [row["title"] for row in app.session_state.rows] == ["capa", "mapa"]
