"""Private progress-photo journal. Only authenticated JPEG bytes reach the browser."""
import base64
from datetime import date
from html import escape
from io import BytesIO
from uuid import uuid4

import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

BUCKET = "solem-progress-photos"
MAX_INPUT = 8 * 1024 * 1024
MAX_JPEG = 4 * 1024 * 1024


def normalized_jpeg(raw):
    """Resize and re-encode to discard EXIF/location and unsupported image data."""
    if not 0 < len(raw) <= MAX_INPUT:
        raise ValueError("Selecione uma imagem de até 8 MB.")
    try:
        with Image.open(BytesIO(raw)) as source:
            if source.format not in ("JPEG", "PNG", "WEBP") or source.width * source.height > 20_000_000:
                raise ValueError("Use JPG, PNG ou WebP com até 20 megapixels.")
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((1600, 1600))
            for quality in (84, 72, 58):
                output = BytesIO()
                image.save(output, "JPEG", quality=quality, optimize=True)
                if output.tell() <= MAX_JPEG:
                    return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("O arquivo não é uma imagem válida.") from error
    raise ValueError("A imagem ficou grande demais após o processamento. Escolha outra foto.")


def _list(client):
    rows = []
    while True:
        page = client.table("solem_photos").select("id,day,kind,file_path,created_at").order(
            "day", desc=True).order("created_at", desc=True).range(len(rows), len(rows) + 499).execute().data
        rows.extend(page)
        if len(page) < 500:
            return rows


def _picture(client, row, label):
    try:
        data = client.storage.from_(BUCKET).download(row["file_path"])
        if not data.startswith(b"\xff\xd8\xff") or len(data) > MAX_JPEG:
            raise ValueError("Arquivo inválido")
    except Exception:
        st.warning("Não foi possível abrir esta foto. Confira a sessão e a conexão.")
        return
    source = base64.b64encode(data).decode("ascii")
    st.html(f'<figure class="progress-photo"><img src="data:image/jpeg;base64,{source}" '
            f'alt="{escape(label)}"/><figcaption>{escape(label)}</figcaption></figure>')


def photo_journal(day, demo=False):
    st.caption("Uma foto de rosto e uma de corpo por dia, opcionais. Armazenamento privado; o app remove metadados EXIF, inclusive localização, antes do envio.")
    if demo:
        st.info("Fotos privadas não são enviadas no modo demonstração.")
        return
    client = st.session_state.get("private_client")
    if client is None:
        st.error("Entre novamente para acessar fotos privadas.")
        return
    try:
        user = client.auth.get_user().user
        rows = _list(client)
    except Exception:
        st.warning("O diário de fotos ainda precisa ser ativado no Supabase, ou sua sessão expirou. Execute a migração 20260923_health_photos.sql no mesmo projeto.")
        return
    existing = {(str(row["day"]), row["kind"]): row for row in rows}
    with st.form("photo_upload", clear_on_submit=True):
        kind = st.selectbox("Foto para o dia selecionado", ["Rosto", "Corpo"])
        upload = st.file_uploader("Imagem JPG, PNG ou WebP", type=["jpg", "jpeg", "png", "webp"],
                                  key="health_photo_upload")
        submitted = st.form_submit_button("Salvar foto privada", use_container_width=True)
    if submitted:
        code = "face" if kind == "Rosto" else "body"
        if upload is None:
            st.error("Selecione uma foto antes de salvar.")
        elif (str(day), code) in existing:
            st.error("Já existe uma foto deste tipo neste dia. Remova-a antes de enviar outra.")
        else:
            try:
                image = normalized_jpeg(upload.getvalue())
                photo_id = str(uuid4())
                path = f"{user.id}/{photo_id}.jpg"
                inserted = client.table("solem_photos").insert({"id": photo_id, "day": str(day),
                    "kind": code, "file_path": path}).execute().data
                if not inserted:
                    raise ValueError("Não foi possível confirmar a foto.")
                try:
                    client.storage.from_(BUCKET).upload(path, image, {"content-type":"image/jpeg", "upsert":"false"})
                except Exception:
                    client.table("solem_photos").delete().eq("id", photo_id).execute()
                    raise
            except ValueError as error:
                st.error(str(error))
            except Exception:
                st.error("Não foi possível enviar a foto. Confira a conexão e tente novamente.")
            else:
                st.session_state["solem_feedback"] = "Foto privada salva."
                st.rerun()
    if not rows:
        st.info("Sua linha do tempo começa quando você adicionar a primeira foto.")
        return
    days = sorted({date.fromisoformat(str(row["day"])) for row in rows})
    st.subheader("Comparar evolução")
    start_col, end_col = st.columns(2)
    with start_col:
        start = st.selectbox("Data inicial", days, index=0, format_func=lambda value: value.strftime("%d/%m/%Y"))
    with end_col:
        end = st.selectbox("Data final", days, index=len(days)-1, format_func=lambda value: value.strftime("%d/%m/%Y"))
    for code, label in (("face", "Rosto"), ("body", "Corpo")):
        st.markdown(f"#### {label}")
        before, after = st.columns(2)
        for column, selected, caption in ((before, start, "Antes"), (after, end, "Depois")):
            with column:
                row = existing.get((str(selected), code))
                if row:
                    _picture(client, row, f"{caption} · {label} · {selected:%d/%m/%Y}")
                else:
                    st.caption(f"Sem foto de {label.lower()} em {selected:%d/%m/%Y}.")
    st.divider()
    chosen = st.selectbox("Foto para remover", rows,
        format_func=lambda row: f"{str(row['day'])[:10]} · {'Rosto' if row['kind']=='face' else 'Corpo'}")
    confirmed = st.checkbox("Confirmo que quero remover esta foto permanentemente")
    if st.button("Remover foto", disabled=not confirmed):
        try:
            client.storage.from_(BUCKET).remove([chosen["file_path"]])
            client.table("solem_photos").delete().eq("id", chosen["id"]).execute()
        except Exception:
            st.error("Não foi possível remover a foto. Confira a conexão e tente novamente.")
        else:
            st.session_state["solem_feedback"] = "Foto removida."
            st.rerun()
