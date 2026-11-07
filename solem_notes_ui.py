"""Folder navigation and an inline document canvas for private notes."""
import json
from pathlib import Path
from uuid import uuid4
import streamlit as st
import streamlit.components.v1 as components
from solem_notes import FOLDER_PREFIX, folder_data, document_data, image_assets, save_note
from solem_note_materials import material

_editor = components.declare_component("solem_note_editor", path=str(Path(__file__).parent / "assets/note_editor"))


def notes_library(repo, items):
    from solem_workspace_ui import safe_error
    folders = {row["id"]: row for row in items if folder_data(row) is not None}
    notes = [row for row in items if row["kind"] == "note" and not material(row) and folder_data(row) is None]
    docs = {row["id"]: document_data(row, items) for row in notes}
    if "notes_folder" not in st.session_state:
        st.session_state.notes_folder = ""
    folder_id = st.session_state.notes_folder
    left, right = st.columns([1, 3], gap="large")
    with left:
        st.markdown("##### Biblioteca")
        search = st.text_input("Buscar anotações", key="notes_search", placeholder="Buscar anotações…", label_visibility="collapsed")
        trash = st.toggle("Lixeira", key="notes_trash")
        if st.button("Todas as anotações", use_container_width=True):
            st.session_state.notes_folder = ""
            st.session_state.pop("notes_selected", None)
            st.rerun()
        with st.popover("＋ Nova pasta", use_container_width=True):
            with st.form("notes_new_folder"):
                name = st.text_input("Nome da pasta", max_chars=160)
                if st.form_submit_button("Criar pasta"):
                    try:
                        saved = repo.save(dict(kind="note", title=name.strip(), body=FOLDER_PREFIX+"{}"),
                                          new_id=st.session_state.setdefault("notes_folder_draft", str(uuid4())))
                        st.session_state.notes_folder = saved["id"]
                        st.session_state.pop("notes_folder_draft", None)
                        st.session_state.pop("notes_selected", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(safe_error(exc))
        for row in folders.values():
            if row.get("archived", False) != trash:
                continue
            label, actions = st.columns([4, 1])
            if label.button(row["title"], icon=":material/folder:", key="folder_open_"+row["id"], use_container_width=True):
                st.session_state.notes_folder = row["id"]
                st.session_state.pop("notes_selected", None)
                st.rerun()
            with actions.popover("⋯", help="Ações da pasta "+row["title"]):
                with st.form("rename_"+row["id"]):
                    title = st.text_input("Renomear pasta", row["title"], max_chars=160)
                    if st.form_submit_button("Renomear"):
                        try:
                            repo.save(dict(kind="note", title=title.strip(), body=row["body"]), old=row)
                            st.rerun()
                        except Exception as exc:
                            st.error(safe_error(exc))
                if st.button("Restaurar pasta" if trash else "Mover pasta para a lixeira", key="archive_folder_"+row["id"]):
                    try:
                        repo.archive(row, not trash)
                        st.session_state.notes_folder = ""
                        st.session_state.pop("notes_selected", None)
                        st.rerun()
                    except Exception as exc:
                        st.error(safe_error(exc))
        st.divider()
        if st.button("＋ Nova anotação", disabled=trash, use_container_width=True):
            note_id = str(uuid4())
            st.session_state.notes_selected = note_id
            st.session_state["note_draft_"+note_id] = dict(title="", folder=folder_id,
                blocks=[dict(id=str(uuid4()), type="text", text="")], images={}, base=None, reset=str(uuid4()))
            st.rerun()
        visible = []
        for row in notes:
            parent = folders.get(docs[row["id"]]["folder"], {})
            is_trash = row.get("archived", False) or parent.get("archived", False)
            text = row["title"]+" "+" ".join(b.get("text", "") for b in docs[row["id"]]["blocks"])
            if is_trash == trash and (not folder_id or docs[row["id"]]["folder"] == folder_id) and search.casefold() in text.casefold():
                visible.append(row)
                if st.button(row["title"], icon=":material/description:", key="note_open_"+row["id"], use_container_width=True):
                    st.session_state.notes_selected = row["id"]
                    st.rerun()
        if not visible:
            st.caption("Nenhuma anotação aqui.")
    with right:
        note_id = st.session_state.get("notes_selected")
        old = next((row for row in notes if row["id"] == note_id), None)
        if not note_id:
            st.subheader(folders.get(folder_id, {}).get("title", "Suas anotações"))
            st.write("Crie uma anotação ou abra uma página da biblioteca.")
            return
        if old and (old.get("archived") or folders.get(docs[note_id]["folder"], {}).get("archived")):
            st.subheader(old["title"])
            if folders.get(docs[note_id]["folder"], {}).get("archived"):
                st.info("Restaure a pasta para abrir esta anotação.")
            elif st.button("Restaurar anotação"):
                try:
                    repo.archive(old, False)
                    st.rerun()
                except Exception as exc:
                    st.error(safe_error(exc))
            return
        draft_key = "note_draft_"+note_id
        if draft_key not in st.session_state:
            data = document_data(old, items)
            st.session_state[draft_key] = dict(title=old["title"], **data, images=image_assets(note_id, items), base=old, reset=str(uuid4()))
        draft = st.session_state[draft_key]
        toolbar, actions = st.columns([4, 1])
        available = {"": "Sem pasta", **{key: row["title"] for key, row in folders.items() if not row.get("archived")}}
        previous_folder = draft["folder"]
        draft["folder"] = toolbar.selectbox("Pasta da anotação", list(available),
            index=list(available).index(draft["folder"]) if draft["folder"] in available else 0,
            format_func=available.get, key="note_location_"+note_id)
        if previous_folder != draft["folder"]:
            draft["saved"] = False
        with actions.popover("⋯", help="Ações da anotação"):
            if old and st.button("Mover para a lixeira", key="note_archive_"+note_id):
                try:
                    repo.archive(old, True)
                    st.session_state.pop("notes_selected", None)
                    st.rerun()
                except Exception as exc:
                    st.error(safe_error(exc))
            if old and st.button("Recarregar versão salva", key="note_reload_"+note_id):
                st.session_state.pop(draft_key, None)
                st.session_state.pop("note_location_"+note_id, None)
                st.rerun()
        event = _editor(title=draft["title"], blocks=draft["blocks"], images=draft["images"], reset=draft["reset"],
                        saved=draft.get("saved", False), error=draft.get("error", ""), key="note_editor_"+note_id, default=None)
        if event and event.get("event") != draft.get("event"):
            draft.update(title=event["title"], blocks=event["blocks"], images=event["images"],
                         event=event["event"], saved=False, error="")
            if event["action"] == "save":
                try:
                    saved = save_note(repo, note_id, draft["title"], draft["folder"], draft["blocks"], draft["images"], items, draft["base"])
                    draft.update(base=saved, saved=True)
                except Exception as exc:
                    draft["error"] = safe_error(exc)
                st.rerun()
