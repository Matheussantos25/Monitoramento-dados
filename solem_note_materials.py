"""Private materials attached to an existing note; each material has its own revision and trash state."""
import base64
import io
import json
from pathlib import PurePath
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import UUID, uuid4, uuid5

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


def folder_images(uploads, folder_id, draft, title=""):
    if not 1 <= len(uploads) <= 20:
        raise ValueError("Selecione de 1 a 20 imagens por vez.")
    rows = []
    for index, upload in enumerate(uploads, 1):
        name = PurePath(upload.name).stem.strip() or f"Imagem {index}"
        upload.seek(0)
        try:
            image = compact_image(upload)
        except (OSError, ValueError, Image.DecompressionBombError) as exc:
            raise ValueError(f"Confira o arquivo {upload.name}. Use uma imagem válida de até 24 megapixels.") from exc
        label = title.strip() or name
        if title.strip() and len(uploads) > 1:
            label = f"{label[:150]} · {index}"
        digest = sha256(image.encode("ascii")).hexdigest()
        row_id = uuid5(UUID(draft), f"{index}/{name}/{digest}")
        body = PREFIX + json.dumps(dict(folder=folder_id, type="image", value=image))
        rows.append(dict(id=str(row_id), kind="note", title=label[:160], body=body))
    return rows


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
            title = st.text_input("Título das imagens (opcional)" if kind == "image" else "Título do material", max_chars=160)
            if kind == "image":
                uploads = st.file_uploader("Selecionar imagens", type=["jpg", "jpeg", "png", "webp"],
                                          accept_multiple_files=True, max_upload_size=10,
                                          help="Escolha até 20 imagens. O nome de cada arquivo será usado como título se deixar o campo vazio.")
            elif kind == "link":
                value = st.text_input("Endereço do link", placeholder="https://", max_chars=2000).strip()
            else:
                value = st.text_area("Referência ou trecho", max_chars=16000).strip()
            if st.form_submit_button("Adicionar imagens à pasta" if kind == "image" else "Adicionar material"):
                try:
                    if kind == "image":
                        rows = folder_images(uploads, folder["id"], draft, title)
                        repo.add_folder_images(rows)
                        message = f"Imagens adicionadas à pasta: {len(rows)}."
                    else:
                        if not title.strip():
                            raise ValueError("Dê um título ao material.")
                        if not value or (kind == "link" and not web_link(value)):
                            raise ValueError("Informe uma referência ou um link http/https válido.")
                        body = PREFIX + json.dumps(dict(folder=folder["id"], type=kind, value=value), ensure_ascii=False)
                        repo.save(dict(kind="note", title=title.strip(), body=body), new_id=draft)
                        message = "Material adicionado à pasta."
                    st.session_state[key+"_draft"] = str(uuid4())
                    st.session_state.ws_feedback = message
                    st.rerun()
                except Exception as exc:
                    st.error(safe_error(exc))
