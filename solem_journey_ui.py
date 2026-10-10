"""RPG missions and private multi-channel production workspace for Streamlit."""
import json
import base64
import time
from datetime import date
from html import escape
from pathlib import Path
import streamlit as st
from solem_health import now_local
from solem_journey import (ACCENTS, GOALS, STAGES, CREATOR_LIMITS, CREATOR_RANKS,
                           JourneyStore, creator_progress, preferences)
from solem_workspace import mind_nodes


def store():
    demo = st.session_state.get("journey_is_demo", False)
    return JourneyStore(st.session_state.get("private_client"),
                        st.session_state if demo else None,
                        "generic" if st.session_state.get("generic_account") else "personal")


def refresh():
    st.session_state.pop("journey_loaded_at", None)


def load_journey(personal, generic, demo):
    st.session_state["journey_personal"] = personal
    st.session_state["journey_is_demo"] = demo
    editing = st.session_state.get("solem_page") == "Metas e aparência" or st.session_state.get("creator_editor")
    if "journey_loaded_at" in st.session_state and (editing or time.monotonic() - st.session_state["journey_loaded_at"] < 30):
        return
    try:
        repo = store()
        data = repo.load()
        if demo and personal and not any(r["kind"] == "channel" for r in data["items"]):
            repo.save_item(dict(kind="channel", title="Canal principal · Gacha", body="Meu canal principal de vídeos Gacha."))
            data = repo.load()
        prefs = preferences((data["settings"] or {}).get("preferences"), personal, generic)
        st.session_state["journey_data"] = data
        st.session_state["journey_preferences"] = prefs
        st.session_state["journey_error"] = False
    except Exception:
        # Do not turn a network/auth/schema failure into an apparent zero count.
        st.session_state["journey_data"] = None
        st.session_state["journey_preferences"] = preferences(personal=personal, generic=generic)
        st.session_state["journey_error"] = True
    st.session_state["journey_loaded_at"] = time.monotonic()


def theme():
    prefs = st.session_state.get("journey_preferences", preferences())
    accent = ACCENTS[prefs["accent"]]
    st.html("<style>" + (Path(__file__).parent / "assets/journey.css").read_text(encoding="utf8") +
            f":root {{ --journey-accent: {accent}; --accent: {accent}; }}" +
            (".rank-promotion {display:none!important;}" if not prefs["effects"] else "") + "</style>")


def _ready():
    if not st.session_state.get("journey_data"):
        st.warning("Não foi possível carregar suas metas e seus canais. Nenhum dado foi alterado.")
        st.button("Tentar novamente", key="journey_retry", on_click=refresh)
        return False
    return True


def _save(action, message):
    try:
        action()
    except ValueError as error:
        st.error(str(error))
        return
    except Exception:
        st.error("Não foi possível confirmar a alteração. Verifique a conexão ou entre novamente e atualize antes de tentar outra vez.")
        return
    refresh()
    dismiss_creator()
    st.session_state["solem_feedback"] = message
    st.rerun()


def mission_summary(goals):
    prefs = st.session_state.get("journey_preferences", preferences())
    data = st.session_state.get("journey_data")
    valid = [g for g in goals if g["value"] is not None]
    done = sum(g["done"] for g in valid)
    coverage = sum(min(1, g["value"] / g["target"]) for g in valid) / len(valid) if valid else 0
    st.html(f'''<section class="journey-command" aria-label="Missões do dia">
        <div><span class="eyebrow">SEU DIA / SUA MISSÃO</span><h2>{'Missão cumprida.' if goals and done == len(goals) else 'Faça o próximo movimento.'}</h2>
        <p>Corpo em movimento. Ideias no mundo. Cada registro aproxima você da sua meta.</p></div>
        <div class="journey-score"><strong>{coverage:.0%}</strong><span>{done} / {len(goals)} missões concluídas</span></div>
        <progress max="100" value="{coverage*100:.1f}" aria-label="Progresso médio das metas disponíveis"></progress>
    </section>''')
    if len(valid) != len(goals):
        st.caption("Progresso parcial: há fontes indisponíveis. Elas não foram contadas como zero.")
    if not goals:
        st.info("Escolha suas missões em Metas e aparência para começar.")
    from solem_ui import navigate
    a, b = st.columns(2)
    a.button("Personalizar minhas metas", key="journey_customize", on_click=navigate, args=("Metas e aparência",), use_container_width=True)
    b.button("Abrir meu estúdio", key="journey_open_creator", on_click=navigate, args=("Criador",), use_container_width=True)
    if data is not None and any(k in prefs["enabled"] for k in ("created", "published")):
        creator_badge(creator_progress(data["items"], now_local().date()))
    # A celebration only follows a verified change in this session, never login.
    checkpoint = (str(now_local().date()), tuple(sorted((g["id"], g["target"]) for g in goals)))
    prior = st.session_state.get("journey_day_completion")
    complete = bool(goals) and done == len(goals)
    if prior and prior[0] == checkpoint and not prior[1] and complete:
        st.toast("Missões do dia concluídas. Seu esforço virou resultado!", icon=":material/verified:")
        if prefs["effects"]:
            st.html('<section class="rank-promotion" role="status"><div class="rank-promotion__veil"></div><div class="rank-promotion__rays"></div><div class="rank-promotion__ring"></div><div class="rank-promotion__content"><span>MISSÕES DO DIA</span><h2>Missão cumprida.</h2><p>Seu esforço virou resultado.</p></div></section>')
        if prefs["sound"]:
            from solem_ranks_ui import promotion_sound
            with st.container(key="rank_promotion_audio"):
                st.audio(promotion_sound(), autoplay=True)
    st.session_state["journey_day_completion"] = (checkpoint, complete or bool(prior and prior[0] == checkpoint and prior[1]))


def creator_badge(stats):
    tier = stats["tier"]
    art = base64.b64encode((Path(__file__).parent / f"assets/ranks/rank_{tier}.svg").read_bytes()).decode()
    target = CREATOR_LIMITS[tier + 1] if tier + 1 < len(CREATOR_LIMITS) else None
    level_progress = (stats["xp"] - CREATOR_LIMITS[tier]) / (target - CREATOR_LIMITS[tier]) if target else 1
    st.html(f'''<section class="creator-rank"><div class="creator-rank__identity"><img width="84" alt="Insígnia da trilha do criador" src="data:image/svg+xml;base64,{art}"/><div><span class="eyebrow">TRILHA DO CRIADOR</span><h3>{escape(stats['rank'])}</h3>
        <p>{stats['xp']} XP de criação · {stats['pipeline']} ideias em produção</p></div></div>
        <div><span>{f'Próximo elo: {CREATOR_RANKS[tier+1]}' if target else 'Elo máximo alcançado'}</span>
        <progress max="100" value="{level_progress*100:.1f}" aria-label="Progresso do elo de criação"></progress>
        <small>{f'Faltam {target-stats["xp"]} XP' if target else 'Continue criando no seu ritmo'}</small></div></section>''')
    previous = st.session_state.get("creator_rank_high_water", tier)
    st.session_state["creator_rank_high_water"] = max(tier, previous)
    prefs = st.session_state["journey_preferences"]
    if tier > previous:
        from solem_ranks_ui import promotion_overlay, promotion_sound
        if prefs["effects"]:
            promotion_overlay(tier, "Trilha do criador", title=stats['rank'])
        if prefs["sound"]:
            with st.container(key="creator_promotion_audio"):
                st.audio(promotion_sound(), autoplay=True)


def settings_page():
    st.title("Metas e aparência")
    st.caption("Seu painel, suas prioridades. Alterar metas não edita seus registros nem apaga XP.")
    if not _ready():
        return
    prefs = st.session_state["journey_preferences"]
    data = st.session_state["journey_data"]
    allowed = [k for k in GOALS if k != "mewing" or not st.session_state.get("generic_account")]
    with st.form("journey_settings_form"):
        enabled = st.multiselect("Missões que aparecem no check-up", allowed,
                                 default=prefs["enabled"], format_func=lambda k: GOALS[k][0], key="journey_enabled")
        st.caption("Metas diárias. Você pode desativar uma missão sem perder os registros correspondentes.")
        values = dict(prefs["targets"])
        columns = st.columns(2)
        for i, key in enumerate(allowed):
            label, unit, _, maximum = GOALS[key]
            with columns[i % 2]:
                kwargs = dict(min_value=0.1, max_value=float(maximum), step=0.5, value=float(values[key])) if key == "cardio" else dict(min_value=1, max_value=maximum, step=1, value=int(values[key]))
                values[key] = st.number_input(f"{label} por dia ({unit})", key=f"target_{key}", **kwargs)
        accent = st.selectbox("Cor de destaque", list(ACCENTS), index=list(ACCENTS).index(prefs["accent"]), key="journey_accent")
        effects = st.checkbox("Animações de conquista", value=prefs["effects"])
        sound = st.checkbox("Sons de conquista", value=prefs["sound"])
        st.caption("O navegador pode pedir interação antes de reproduzir som. A preferência de movimento reduzido do dispositivo é respeitada.")
        submitted = st.form_submit_button("Salvar minhas metas", type="primary")
    if submitted:
        def save():
            new = preferences(dict(prefs, targets=values, enabled=enabled, accent=accent, effects=effects, sound=sound),
                              st.session_state["journey_personal"], st.session_state["generic_account"])
            store().save_settings(new, data["settings"])
        _save(save, "Metas e aparência salvas na sua conta.")
    st.info("Consistência não exige treinar com dor ou ignorar recuperação. Ajuste as metas à sua rotina; descansar não remove conquistas.")


def dismiss_creator():
    st.session_state.pop("creator_editor", None)


def open_creator(kind, row=None):
    st.session_state["creator_editor"] = (kind, row)


@st.dialog("Meu canal", width="large", on_dismiss=dismiss_creator)
def channel_editor(row=None):
    row = row or {}
    with st.form(f"creator_channel_{row.get('id', 'new')}"):
        title = st.text_input("Nome do canal", value=row.get("title", ""), max_chars=160)
        body = st.text_area("Público, proposta e ideias do canal", value=row.get("body", ""), max_chars=10000)
        url = st.text_input("Link do canal (opcional)", value=row.get("url", ""), max_chars=2000)
        submitted = st.form_submit_button("Salvar canal", type="primary")
    if submitted:
        _save(lambda: store().save_item(dict(kind="channel", title=title, body=body, url=url), row or None), "Canal salvo.")
    if st.button("Cancelar", key="channel_cancel"):
        dismiss_creator()
        st.rerun()


@st.dialog("Meu vídeo", width="large", on_dismiss=dismiss_creator)
def video_editor(channels, row=None):
    row = row or {}
    key = row.get("id", "new")
    today = now_local().date()
    stage = st.selectbox("Etapa de produção", STAGES, index=STAGES.index(row.get("stage", "Ideia")), key=f"video_stage_{key}")
    # Ordinary widgets preserve the draft when the stage reveals date fields.
    # Nothing is persisted until the explicit save action.
    with st.container():
        ids = [c["id"] for c in channels]
        names = {c["id"]: c["title"] for c in channels}
        channel = st.selectbox("Canal", ids, format_func=names.get, index=ids.index(row["channel_id"]) if row.get("channel_id") in ids else 0)
        title = st.text_input("Título ou ideia do vídeo", value=row.get("title", ""), max_chars=160)
        body = st.text_area("Roteiro e anotações", value=row.get("body", ""), max_chars=10000)
        production = publication = None
        if stage in ("Pronto", "Publicado"):
            production = st.date_input("Data em que ficou pronto", value=date.fromisoformat(row["produced_on"]) if row.get("produced_on") else today, max_value=today)
        if stage == "Publicado":
            publication = st.date_input("Data da publicação", value=date.fromisoformat(row["published_on"]) if row.get("published_on") else today, max_value=today)
        url = st.text_input("Link do vídeo (opcional)", value=row.get("url", ""), max_chars=2000)
        st.caption("Pronto conta na criação. Publicado conta na publicação. Mudar o título ou o canal não cria um novo registro.")
        submitted = st.button("Salvar vídeo", type="primary", key=f"creator_save_video_{key}")
    if submitted:
        _save(lambda: store().save_item(dict(kind="video", title=title, body=body, channel_id=channel,
              stage=stage, produced_on=production, published_on=publication, url=url), row or None), "Vídeo salvo. Suas missões foram atualizadas.")
    if st.button("Cancelar", key="video_cancel"):
        dismiss_creator()
        st.rerun()


def _trash_action(row, restore=False):
    _save(lambda: store().archive(row, not restore), "Registro restaurado." if restore else "Movido para a lixeira. Você pode restaurá-lo.")


def creator_page():
    st.html('<div class="section-intro"><span class="eyebrow">CRIADOR / SEU ESTÚDIO</span><h1>Ideias que viram publicação.</h1><p>Do primeiro roteiro ao vídeo no ar. Organize todos os seus canais aqui.</p></div>')
    if not _ready():
        return
    data = st.session_state["journey_data"]
    items = data["items"]
    active = [r for r in items if not r.get("archived")]
    channels = [r for r in active if r["kind"] == "channel"]
    all_channels = {r["id"]: r for r in items if r["kind"] == "channel"}
    stats = creator_progress(items, now_local().date())
    creator_badge(stats)
    a, b, c = st.columns(3)
    a.metric("Criados hoje", f"{stats['created']} / {st.session_state['journey_preferences']['targets']['created']}")
    b.metric("Publicados hoje", f"{stats['published']} / {st.session_state['journey_preferences']['targets']['published']}")
    c.metric("Publicações · últimos 7 dias", stats["week_published"])
    st.button("Atualizar registros", key="creator_refresh", on_click=refresh)
    videos_tab, channels_tab, map_tab, trash_tab = st.tabs(["Produção", "Canais", "Mapa de ideias", "Lixeira"])
    with videos_tab:
        if not channels:
            st.info("Adicione um canal para começar a registrar seus vídeos.")
        st.button("Novo vídeo", type="primary", disabled=not channels, key="creator_new_video", on_click=open_creator, args=("video",))
        selected = st.selectbox("Filtrar canal", [None] + list(all_channels), format_func=lambda k: "Todos os canais" if k is None else all_channels[k]["title"], key="creator_filter_channel")
        selected_stage = st.selectbox("Filtrar etapa", ["Todas"] + list(STAGES), key="creator_filter_stage")
        videos = [r for r in active if r["kind"] == "video" and (selected is None or r["channel_id"] == selected) and (selected_stage == "Todas" or r["stage"] == selected_stage)]
        if not videos:
            st.info("Nenhum vídeo neste filtro. Comece por uma ideia; marque como Pronto ou Publicado quando concluir.")
        page = st.number_input("Página dos vídeos", min_value=1, max_value=max(1, (len(videos)+9)//10), step=1, key="creator_video_page")
        for row in list(reversed(videos))[(page-1)*10:page*10]:
            with st.container(border=True):
                st.markdown(f"**{escape(row['title'])}**")
                st.caption(f"{all_channels.get(row['channel_id'], {}).get('title', 'Canal')} · {row['stage']}" + (f" · publicado em {row['published_on']}" if row.get('published_on') else ""))
                if row.get("body"):
                    st.text(row["body"][:240])
                edit, trash = st.columns(2)
                edit.button("Editar vídeo", key=f"video_edit_{row['id']}", on_click=open_creator, args=("video", row))
                if trash.button("Mover para lixeira", key=f"video_archive_{row['id']}"):
                    _trash_action(row)
    with channels_tab:
        st.button("Adicionar canal", key="creator_new_channel", on_click=open_creator, args=("channel",))
        for row in channels:
            with st.container(border=True):
                st.subheader(row["title"])
                st.text(row["body"])
                if row.get("url"):
                    st.link_button("Abrir canal", row["url"])
                st.caption("Arquivar o canal não apaga seus vídeos nem altera as publicações já registradas.")
                edit, trash = st.columns(2)
                edit.button("Editar canal", key=f"channel_edit_{row['id']}", on_click=open_creator, args=("channel", row))
                if trash.button("Mover para lixeira", key=f"channel_archive_{row['id']}"):
                    _trash_action(row)
    with map_tab:
        st.subheader("Seu plano, em um mapa")
        st.caption("Use uma linha por ideia e dois espaços para cada nível. Até 80 ideias e 5 níveis. O mapa é planejamento: só vídeos registrados preenchem metas.")
        prefs = st.session_state["journey_preferences"]
        body = st.text_area("Canais, ideias e etapas", value=prefs["strategy"], height=260, max_chars=10000, key="creator_strategy")
        try:
            nodes = mind_nodes(body)
            dot = ['digraph { rankdir=LR; bgcolor="transparent"; node [shape=box,style="rounded,filled",fillcolor="#162840",color="#526880",fontcolor="#E7F1FF"]; edge [color="#83DCFF"];']
            for i, (label, parent, _) in enumerate(nodes):
                dot.append(f'n{i} [label={json.dumps(label, ensure_ascii=False)}];')
                if parent is not None:
                    dot.append(f'n{parent} -> n{i};')
            st.graphviz_chart("\n".join(dot + ["}"]), use_container_width=True)
            valid_map = True
        except ValueError as error:
            st.warning(str(error))
            valid_map = False
        if st.button("Salvar mapa", key="creator_save_map", disabled=not valid_map):
            _save(lambda: store().save_settings(preferences(dict(prefs, strategy=body), st.session_state["journey_personal"], st.session_state["generic_account"]), data["settings"]), "Mapa de ideias salvo.")
    with trash_tab:
        rows = [r for r in items if r.get("archived")]
        st.caption("Nada é apagado definitivamente aqui. Restaurar vídeos recupera seu progresso; canais e vídeos são restaurados separadamente.")
        if not rows:
            st.info("A lixeira está vazia.")
        for row in rows:
            with st.container(border=True):
                st.text(row["title"])
                if st.button("Restaurar", key=f"creator_restore_{row['id']}"):
                    _trash_action(row, True)
    with st.expander("Regras da trilha do criador"):
        st.write("Cada vídeo pronto vale 20 XP; publicado rende mais 30 XP. O mesmo registro pontua uma vez em cada etapa, mesmo após edição. Ideias e datas futuras não pontuam. O total reúne todos os canais e não altera seus pontos antigos de treino ou estudo.")
        st.write("Este é um controle pessoal: o Solem não publica no YouTube nem verifica automaticamente os canais. Registre as etapas que você realmente concluiu.")
        st.dataframe([dict(Elo=name, XP=limit) for name, limit in zip(CREATOR_RANKS, CREATOR_LIMITS)], hide_index=True)
    editor = st.session_state.get("creator_editor")
    if editor:
        kind, row = editor
        if kind == "channel":
            channel_editor(row)
        else:
            editable = list(channels)
            if row and row["channel_id"] not in [c["id"] for c in channels]:
                editable.append(all_channels[row["channel_id"]])
            if editable:
                video_editor(editable, row)
