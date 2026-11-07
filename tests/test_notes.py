import base64
import copy
import json
from uuid import uuid4
import pytest
from solem_notes import *
from solem_note_moves import move_note
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
import solem_notes_library as ui
from solem_notes import FOLDER_PREFIX
ui._library=lambda **kwargs: st.session_state.pop("library_event",None)
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
    app.session_state["library_event"]=dict(event="actions",action="folder_actions",id=folder)
    app.run()
    next(t for t in app.text_input if t.label=="Renomear pasta").set_value("Referências")
    next(b for b in app.button if b.label=="Renomear").click().run()
    app.session_state["library_event"]=dict(event="new",action="new_note")
    app.run()
    app.session_state["editor_event"]=dict(action="save",event="one",title="Página",blocks=BLOCKS,images={IMAGE:JPEG})
    app.run()
    assert not app.exception
    note=next(row for row in app.session_state.rows if row["title"]=="Página")
    assert document_data(note)["folder"]==folder
    assert document_data(note)["blocks"]==BLOCKS
    assert next(row for row in app.session_state.rows if row["id"]==folder)["title"]=="Referências"
    # Moving a saved page keeps the editor draft and rebases only its revision.
    draft=app.session_state["note_draft_"+note["id"]]
    draft["blocks"]=[dict(id="draft",type="text",text="Ainda não salvo")]
    before_count=len(app.session_state.rows)
    app.session_state["library_event"]=dict(event="move",action="move",id=note["id"],destination="",revision=note["revision"])
    app.run()
    moved=next(row for row in app.session_state.rows if row["id"]==note["id"])
    assert document_data(moved)["folder"]==""
    assert document_data(moved)["blocks"]==BLOCKS
    assert len(app.session_state.rows)==before_count
    assert app.session_state["note_draft_"+note["id"]]["blocks"][0]["text"]=="Ainda não salvo"
    assert app.session_state["note_draft_"+note["id"]]["base"]["revision"]==moved["revision"]
    app.session_state["library_event"]=dict(event="move",action="move",id=note["id"],destination="",revision=note["revision"])
    app.run()
    assert next(row for row in app.session_state.rows if row["id"]==note["id"])["revision"]==moved["revision"]
    next(b for b in app.button if b.label=="Mover para a lixeira").click().run()
    assert next(row for row in app.session_state.rows if row["id"]==note["id"])["archived"]


def test_move_legacy_note_preserves_inline_attachments_and_updates_only_original():
    folder=dict(id=FOLDER,kind="note",title="IA",body=FOLDER_PREFIX+"{}")
    class Repo:
        calls=[]
        def save(self,item,old):
            self.calls.append((item,old))
            return dict(old,**item,revision=old["revision"]+1)
    repo=Repo()
    saved=move_note(repo,[OLD,ASSET,folder],NOTE,FOLDER,1)
    assert saved["id"]==NOTE
    assert document_data(saved)["folder"]==FOLDER
    assert document_data(saved)["blocks"]==document_data(OLD,[ASSET])["blocks"]
    assert repo.calls[0][1] is OLD
    assert OLD["body"]=="Texto original"

def test_move_checks_archive_revision_and_preserves_unknown_document_fields():
    folder=dict(id=FOLDER,kind="note",title="IA",body=FOLDER_PREFIX+"{}")
    doc=dict(folder="",blocks=BLOCKS,extra="keep")
    note=dict(OLD,body=DOCUMENT_PREFIX+json.dumps(doc))
    class Repo:
        calls=[]
        def save(self,item,old):
            self.calls.append(item)
            return dict(old,**item)
    repo=Repo()
    for target, revision in [(folder,0),(dict(folder,archived=True),1)]:
        with pytest.raises(ValueError):
            move_note(repo,[note,target],NOTE,FOLDER,revision)
    assert not repo.calls
    saved=move_note(repo,[note,folder],NOTE,FOLDER,1)
    assert json.loads(saved["body"][len(DOCUMENT_PREFIX):])["extra"]=="keep"
    assert document_data(saved)["blocks"]==BLOCKS
    assert move_note(repo,[saved,folder],NOTE,FOLDER,1) is saved
    assert len(repo.calls)==1
