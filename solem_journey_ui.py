"""RPG missions and private multi-channel production workspace for Streamlit."""
import time
from pathlib import Path
import streamlit as st
from solem_health import now_local
from solem_journey import ACCENTS, GOALS, JourneyStore, preferences


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
    b.button("Checklist de publicações", key="journey_open_creator", on_click=navigate, args=("Publicações",), use_container_width=True)
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


def settings_page():
    st.title("Metas e aparência")
    st.caption("Seu painel, suas prioridades. Alterar metas não edita seus registros nem apaga XP.")
    if not _ready():
        return
    prefs = st.session_state["journey_preferences"]
    data = st.session_state["journey_data"]
    allowed = [k for k in GOALS if k != "created" and (not st.session_state.get("generic_account") or k in ("water", "flexao", "agachamento", "cardio"))]
    with st.form("journey_settings_form"):
        enabled = st.multiselect("Missões que aparecem no check-up", allowed,
                                 default=prefs["enabled"], format_func=lambda k: GOALS[k][0], key="journey_enabled")
        st.caption("Metas diárias. Você pode desativar uma missão sem perder os registros correspondentes.")
        st.caption("O check-up mostra as missões ativadas aqui, com os valores que você salvar. O plano de treino tem metas próprias e não oculta nem substitui suas escolhas.")
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


def _trash_action(row, restore=False):
    _save(lambda: store().archive(row, not restore), "Registro restaurado." if restore else "Movido para a lixeira.")


def creator_page():
    from solem_publications_ui import publications_page
    publications_page()
