"""Private materials attached to an existing note; each material has its own revision and trash state."""
import base64
import io
import json
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import streamlit as st
from PIL import Image, ImageOps

PREFIX = "solem-note-material-v1\n"


def material(item):
    body = item.get("body", "")
    if item.get("kind") != "note" or not body.startswith(PREFIX):
        return None
    try:
        data = json.loads(body[len(PREFIX):])
        UUID(data["folder"])
        if data["type"] in ("image", "link", "reference") and isinstance(data["value"], str):
            return data
    except (AttributeError, KeyError, TypeError, ValueError):
        pass
    return None


def web_link(value):
    url = urlsplit(value)
    return url.scheme in ("https", "http") and bool(url.hostname)


def compact_image(upload):
    if upload is None:
        raise ValueError("Escolha uma imagem.")
    with Image.open(upload) as source:
        if source.width * source.height > 24_000_000:
            raise ValueError("Escolha uma imagem com até 24 megapixels.")
        source.thumbnail((1200, 1200))
        picture = ImageOps.exif_transpose(source).convert("RGB")
    while True:
        output = io.BytesIO()
        picture.save(output, "JPEG", quality=80, optimize=True)
        if output.tell() <= 35000:
            return base64.b64encode(output.getvalue()).decode("ascii")
        picture.thumbnail((max(1, picture.width * 3 // 4), max(1, picture.height * 3 // 4)))


def folder_panel(repo, folder, materials):
    from solem_workspace_ui import safe_error
    with st.expander("Pasta de materiais · imagens, links e referências", expanded=True):
        own = [(row, data) for row, data in materials if data["folder"] == folder["id"]]
        key = "material_" + folder["id"]
        trash = st.toggle("Lixeira desta pasta", key=key+"_trash")
        for row, data in own:
            if row["archived"] != trash:
                continue
            with st.expander(row["title"]):
                if not trash:
                    if data["type"] == "image":
                        st.image(base64.b64decode(data["value"]), caption=row["title"])
                    elif data["type"] == "link" and web_link(data["value"]):
                        st.link_button("Abrir link", data["value"])
                    else:
                        st.text(data["value"])
                if st.button("Restaurar material" if trash else "Mover material para a lixeira", key="trash_"+row["id"]):
                    try:
                        repo.archive(row, not trash)
                        st.rerun()
                    except Exception as exc:
                        st.error(safe_error(exc))
        if trash:
            return
        kinds = {"Imagem": "image", "Link": "link", "Referência": "reference"}
        kind = kinds[st.radio("Adicionar à pasta", list(kinds), horizontal=True, key=key+"_type")]
        draft = st.session_state.setdefault(key+"_draft", str(uuid4()))
        with st.form(key+"_"+kind+"_"+draft):
            title = st.text_input("Título do material", max_chars=160)
            if kind == "image":
                upload = st.file_uploader("Imagem · uma cópia compacta será salva", type=["jpg","jpeg","png","webp"], max_upload_size=10)
            elif kind == "link":
                value = st.text_input("Endereço do link", placeholder="https://", max_chars=2000).strip()
            else:
                value = st.text_area("Referência ou trecho", max_chars=16000).strip()
            if st.form_submit_button("Adicionar material"):
                try:
                    if not title.strip():
                        raise ValueError("Dê um título ao material.")
                    if kind == "image":
                        value = compact_image(upload)
                    if not value or (kind == "link" and not web_link(value)):
                        raise ValueError("Informe uma referência ou um link http/https válido.")
                    body = PREFIX + json.dumps(dict(folder=folder["id"], type=kind, value=value), ensure_ascii=False)
                    repo.save(dict(kind="note", title=title.strip(), body=body), new_id=draft)
                    st.session_state[key+"_draft"] = str(uuid4())
                    st.session_state.ws_feedback = "Material adicionado à pasta."
                    st.rerun()
                except Exception as exc:
                    st.error(safe_error(exc))
