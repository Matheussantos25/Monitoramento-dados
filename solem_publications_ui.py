"""Simple posting checklist over the existing private creator records."""
from datetime import date
from uuid import uuid4
import streamlit as st
from solem_health import now_local
from solem_journey import creator_progress
from solem_journey_ui import store, refresh, _ready, _save, _trash_action, open_creator, dismiss_creator, channel_editor


def publication_checklist(compact=False):
    if not _ready():
        return
    items = st.session_state["journey_data"]["items"]
    channels = [r for r in items if r["kind"] == "channel" and not r.get("archived")]
    names = {r["id"]: r["title"] for r in items if r["kind"] == "channel"}
    prefix = "quick_posts" if compact else "daily_posts"
    day = now_local().date() if compact else st.date_input("Dia do checklist", value=now_local().date(), max_value=now_local().date(), key="publication_day")
    rows = [r for r in items if r["kind"] == "video" and not r.get("archived")
            and r.get("stage") == "Publicado" and r.get("published_on") == str(day)]
    target = int(st.session_state["journey_preferences"]["targets"]["published"])
    st.caption(f"{len(rows)} de {target} vídeos publicados · todos os canais")
    channel = None
    if channels:
        channel = st.selectbox("Canal para a próxima publicação", [c["id"] for c in channels],
                               format_func=names.get, key=prefix+"_channel") if len(channels) > 1 else channels[0]["id"]
        if len(channels) == 1:
            st.caption(channels[0]["title"])
    for index, row in enumerate(rows):
        checked = st.checkbox(f"Vídeo {index + 1} publicado", value=True,
                              help=f"{row['title']} · {names.get(row['channel_id'], 'Canal')}",
                              key=f"{prefix}_{row['id']}_{row['revision']}")
        if not checked:
            _trash_action(row)
    for slot in range(len(rows), target):
        if st.checkbox(f"Vídeo {slot + 1} publicado", key=f"{prefix}_{day}_slot_{slot}", disabled=not channels):
            revision = sum(r.get("revision", 0) for r in items)
            operation = f"publication_operation_{day}_{channel}_{slot}_{len(items)}_{revision}"
            record_id = st.session_state.setdefault(operation, str(uuid4()))
            values = dict(kind="video", title=f"Vídeo {slot + 1} · {day:%d/%m/%Y}", channel_id=channel,
                          stage="Publicado", produced_on=str(day), published_on=str(day))
            _save(lambda: store().save_item(values, new_id=record_id), "Publicação registrada.")
    if not channels:
        st.info("Adicione um canal em Publicações para usar o checklist.")
    st.caption("Marque depois de postar. Desmarcar move apenas aquela publicação para a lixeira.")


@st.dialog("Publicação", width="large", on_dismiss=dismiss_creator)
def publication_editor(channels, row):
    today = now_local().date()
    with st.form(f"publication_edit_{row['id']}"):
        ids = [c["id"] for c in channels]
        names = {c["id"]: c["title"] for c in channels}
        channel = st.selectbox("Canal", ids, format_func=names.get, index=ids.index(row["channel_id"]))
        title = st.text_input("Título (opcional)", value=row["title"], max_chars=160)
        posted = st.checkbox("Vídeo publicado", value=row.get("stage") == "Publicado")
        publication = st.date_input("Data da publicação", value=date.fromisoformat(row["published_on"]) if row.get("published_on") else today, max_value=today)
        url = st.text_input("Link (opcional)", value=row.get("url", ""), max_chars=2000)
        submitted = st.form_submit_button("Salvar publicação", type="primary")
    if submitted:
        production = min(row.get("produced_on") or str(publication), str(publication))
        values = dict(row, title=title.strip() or f"Vídeo · {publication:%d/%m/%Y}",
                      channel_id=channel, url=url, stage="Publicado" if posted else row.get("stage", "Ideia"),
                      produced_on=production if posted else row.get("produced_on"),
                      published_on=str(publication) if posted else None)
        if not posted and values["stage"] == "Publicado":
            values["stage"] = "Pronto"
        _save(lambda: store().save_item(values, row), "Publicação atualizada.")
    if st.button("Cancelar", key="video_cancel"):
        dismiss_creator()
        st.rerun()


def publications_page():
    st.title("Publicações")
    st.caption("Postou? Marque. Sem roteiro, etapas de produção ou campos obrigatórios de criação.")
    if not _ready():
        return
    items = st.session_state["journey_data"]["items"]
    active = [r for r in items if not r.get("archived")]
    channels = [r for r in active if r["kind"] == "channel"]
    all_channels = {r["id"]: r for r in items if r["kind"] == "channel"}
    stats = creator_progress(items, now_local().date())
    with st.container(key="publication_stats"):
        a, b = st.columns(2)
        a.metric("Publicados hoje", f"{stats['published']} / {st.session_state['journey_preferences']['targets']['published']}")
        b.metric("Últimos 7 dias", stats["week_published"])
    st.button("Atualizar registros", key="creator_refresh", on_click=refresh)
    daily, history, channel_tab, trash = st.tabs(["Checklist", "Histórico", "Canais", "Lixeira"])
    with daily:
        publication_checklist()
    with history:
        st.caption("Os registros anteriores continuam aqui, inclusive ideias ainda não publicadas.")
        selected = st.selectbox("Filtrar canal", [None] + list(all_channels),
                                format_func=lambda k: "Todos os canais" if k is None else all_channels[k]["title"], key="creator_filter_channel")
        videos = [r for r in active if r["kind"] == "video" and (selected is None or r["channel_id"] == selected)]
        page = st.number_input("Página dos vídeos", min_value=1, max_value=max(1, (len(videos)+9)//10), step=1, key="creator_video_page")
        if not videos:
            st.info("Suas publicações aparecerão aqui quando você marcar o checklist.")
        for row in list(reversed(videos))[(page-1)*10:page*10]:
            with st.container(border=True):
                st.text(row["title"])
                st.caption(f"{all_channels.get(row['channel_id'], {}).get('title', 'Canal')} · " +
                           (f"Publicado em {row['published_on']}" if row.get("published_on") else "Ainda não publicado"))
                if row.get("body"):
                    with st.expander("Anotações anteriores"):
                        st.text(row["body"])
                edit, delete = st.columns(2)
                edit.button("Editar", key=f"video_edit_{row['id']}", on_click=open_creator, args=("video", row))
                if delete.button("Mover para lixeira", key=f"video_archive_{row['id']}"):
                    _trash_action(row)
        with st.expander("Meu mapa anterior"):
            st.text(st.session_state["journey_preferences"]["strategy"])
    with channel_tab:
        st.button("Adicionar canal", key="creator_new_channel", on_click=open_creator, args=("channel",))
        for row in channels:
            with st.container(border=True):
                st.subheader(row["title"])
                edit, delete = st.columns(2)
                edit.button("Editar canal", key=f"channel_edit_{row['id']}", on_click=open_creator, args=("channel", row))
                if delete.button("Mover para lixeira", key=f"channel_archive_{row['id']}"):
                    _trash_action(row)
    with trash:
        archived = [r for r in items if r.get("archived")]
        st.caption("Nada é apagado definitivamente. Restaurar uma publicação recupera sua contagem.")
        if not archived:
            st.info("A lixeira está vazia.")
        for row in archived:
            with st.container(border=True):
                st.text(row["title"])
                if st.button("Restaurar", key=f"creator_restore_{row['id']}"):
                    _trash_action(row, True)
    editor = st.session_state.get("creator_editor")
    if editor:
        kind, row = editor
        if kind == "channel":
            channel_editor(row)
        elif row["channel_id"] in all_channels:
            editable = channels if row["channel_id"] in [c["id"] for c in channels] else channels + [all_channels[row["channel_id"]]]
            publication_editor(editable, row)
