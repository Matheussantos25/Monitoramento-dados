import base64
import copy
import json
from uuid import uuid4
import pytest
from solem_notes import *
from solem_note_materials import PREFIX

NOTE, FOLDER, IMAGE = [str(uuid4()) for _ in range(3)]
JPEG = base64.b64encode(b"\xff\xd8test").decode()
OLD = dict(id=NOTE, kind="note", title="Antiga", body="Texto original", revision=1)
ASSET = dict(id=IMAGE, kind="note", title="Foto", body=PREFIX+json.dumps(dict(folder=NOTE,type="image",value=JPEG)))
BLOCKS = [dict(id="a",type="text",text="Antes"),dict(id="b",type="image",ref=IMAGE,caption="Foto"),dict(id="c",type="text",text="Depois")]

def test_legacy_projection_preserves_rows_and_does_not_show_failed_uploads():
    rows = [OLD, ASSET]
    before = copy.deepcopy(rows)
    assert [b["type"] for b in document_data(OLD, rows)["blocks"]] == ["text","image"]
    assert rows == before
    pending = dict(ASSET,body=PREFIX+json.dumps(dict(folder=NOTE,type="image",value=JPEG,pending=True)))
    assert len(document_data(OLD,[pending])["blocks"]) == 1

def test_inline_order_folder_and_retry_keep_same_asset_id():
    folder = dict(id=FOLDER,kind="note",title="Ideias",body=FOLDER_PREFIX+"{}")
    item, uploads = prepare_note(NOTE,"Página",FOLDER,BLOCKS,{IMAGE:JPEG},[folder])
    assert document_data(item)["blocks"] == BLOCKS
    assert document_data(item)["folder"] == FOLDER
    assert uploads[0]["id"] == IMAGE
    assert prepare_note(NOTE,"Página",FOLDER,BLOCKS,{IMAGE:JPEG},[folder])[1] == uploads
    assert prepare_note(NOTE,"Página",FOLDER,BLOCKS,{},[folder,*uploads])[1] == []
    with pytest.raises(ValueError):
        prepare_note(NOTE,"Página",FOLDER,BLOCKS,{},[dict(folder,archived=True)])

def test_invalid_note_does_not_upload_and_conflict_does_not_overwrite():
    class Repo:
        uploads = []
        saves = []
        def add_folder_images(self, rows): self.uploads.extend(rows)
        def save(self,item,old,new_id):
            self.saves.append((old,new_id))
            raise ValueError("Revisão alterada")
    repo=Repo()
    with pytest.raises(ValueError):
        save_note(repo,NOTE,"","",BLOCKS,{IMAGE:JPEG},[],OLD)
    assert not repo.uploads and not repo.saves
    with pytest.raises(ValueError,match="Revisão"):
        save_note(repo,NOTE,"Página","",BLOCKS,{IMAGE:JPEG},[],OLD)
    assert repo.saves == [(OLD,NOTE)]
    assert len(document_data(OLD,repo.uploads)["blocks"]) == 1
    assert OLD["body"] == "Texto original"

def test_editor_assets_are_identical_on_web_and_android():
    from pathlib import Path
    assert Path("assets/note_editor/index.html").read_bytes() == Path("android-app/app/src/main/assets/note_editor/index.html").read_bytes()

def test_library_folder_rename_and_inline_save_roundtrip():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string("""
import streamlit as st
import solem_notes_ui as ui
from solem_notes import FOLDER_PREFIX
ui._editor=lambda **kwargs: st.session_state.pop("editor_event",None)
class Repo:
 def save(self,item,old=None,new_id=None):
  row=dict(item,id=old["id"] if old else new_id,revision=(old["revision"]+1 if old else 1),archived=False)
  st.session_state.rows[:]=[x for x in st.session_state.rows if x["id"]!=row["id"]]+[row]
  return row
 def archive(self,item,archived): item["archived"]=archived
 def add_folder_images(self,rows): st.session_state.rows.extend(rows)
ui.notes_library(Repo(),st.session_state.setdefault("rows",[]))
""").run()
    next(t for t in app.text_input if t.label=="Nome da pasta").set_value("Projetos")
    next(b for b in app.button if b.label=="Criar pasta").click().run()
    assert not app.exception
    folder=app.session_state.rows[0]["id"]
    next(t for t in app.text_input if t.label=="Renomear pasta").set_value("Referências")
    next(b for b in app.button if b.label=="Renomear").click().run()
    next(b for b in app.button if b.label=="＋ Nova anotação").click().run()
    app.session_state["editor_event"]=dict(action="save",event="one",title="Página",blocks=BLOCKS,images={IMAGE:JPEG})
    app.run()
    assert not app.exception
    note=next(row for row in app.session_state.rows if row["title"]=="Página")
    assert document_data(note)["folder"]==folder
    assert document_data(note)["blocks"]==BLOCKS
    assert next(row for row in app.session_state.rows if row["id"]==folder)["title"]=="Referências"
    next(b for b in app.button if b.label=="Mover para a lixeira").click().run()
    assert next(row for row in app.session_state.rows if row["id"]==note["id"])["archived"]
