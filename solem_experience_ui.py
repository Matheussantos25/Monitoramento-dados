"""Lightweight onboarding, accessible insight and user-controlled workout media."""
from html import escape
from pathlib import Path
import streamlit as st
from solem_experience import media_link, workout_week


def experience_theme(prefs):
    css = (Path(__file__).parent / "assets/experience.css").read_text(encoding="utf8")
    if prefs.get("comfort", False):
        css += "*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}.rank-promotion{display:none!important}"
    if prefs.get("contrast", False):
        css += ":root{--muted:#dfebfa!important;--text:#fff!important} [data-testid=stCaptionContainer],.stMarkdown p,.eyebrow,.section-intro p{color:#dfebfa!important} button,input,select,textarea{border-color:#a6bcd3!important}"
    if prefs.get("large_text", False):
        css += "html{font-size:19px!important}[data-testid=stCaptionContainer]{font-size:1rem!important}"
    st.html("<style>" + css + "</style>")


def save_preferences(**changes):
    from solem_journey_ui import store, refresh
    from solem_journey import preferences
    data = st.session_state.get("journey_data")
    if data is None:
        st.error("Suas preferências estão indisponíveis. Atualize para tentar novamente.")
        return
    try:
        values = preferences(dict(st.session_state["journey_preferences"], **changes),
                             st.session_state.get("journey_personal", False), st.session_state.get("generic_account", False))
        store().save_settings(values, data["settings"])
    except Exception:
        st.error("Não foi possível salvar. Atualize para conferir suas preferências antes de tentar novamente.")
        return
    refresh()
    st.rerun()


def guide():
    prefs = st.session_state.get("journey_preferences", {})
    with st.expander("Conheça seu Solem · guia rápido", expanded=not prefs.get("guide_done", False)):
        steps = [
            ("Seu ponto de partida", "Na Visão geral, acompanhe suas missões, seu nível e os registros do dia. O progresso vem das atividades que você salva.", "Visão geral"),
            ("Um treino, um registro", "Em Treino, escolha o exercício, consulte a técnica e use cronômetro ou GPS. Cada sessão pode ser editada separadamente.", "Treino"),
            ("Cuide da rotina inteira", "Em Saúde, registre refeições, água, peso e sono. A balança acumulada calcula a porção de cada alimento pela diferença.", "Saúde"),
            ("Veja o que mudou", "Evolução física mostra seu histórico. Compare o que você fez ao longo dos dias, sem transformar descanso em punição.", "Evolução física"),
            ("Um painel que respeita você", "Em Metas e aparência, escolha suas missões e ajuste conforto visual, contraste e tamanho do texto. Ative só o que faz sentido para sua rotina.", "Metas e aparência"),
        ]
        index = st.session_state.get("guide_step", 0) % len(steps)
        title, body, destination = steps[index]
        animate = st.session_state.pop("guide_animate", False) and not prefs.get("comfort", False)
        import base64
        mascot = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 130"><circle cx="60" cy="29" r="18" fill="#b8d9ec"/>
          <path d="M35 65 Q60 45 85 65 L82 103 H38Z" fill="#83dcff"/><path d="M45 102 L42 124 M75 102 L78 124" stroke="#b8d9ec" stroke-width="12" stroke-linecap="round"/>
          <path d="M37 66 L24 87 M83 65 L99 40" stroke="#b8d9ec" stroke-width="11" stroke-linecap="round"/>
          <circle cx="54" cy="28" r="2" fill="#102437"/><circle cx="66" cy="28" r="2" fill="#102437"/><path d="M54 37 Q60 41 66 37" fill="none" stroke="#102437" stroke-width="2"/></svg>"""
        mascot_url = "data:image/svg+xml;base64," + base64.b64encode(mascot.encode()).decode()
        st.html(f'''<section class="solem-guide {'guide-wave' if animate else ''}" aria-label="Guia do aplicativo">
          <img src="{mascot_url}" class="guide-mascot" width="80" alt="" />
          <div><small>GUIA · {index+1} DE {len(steps)}</small><h3>{title}</h3><p>{body}</p></div></section>''')
        a, b = st.columns(2)
        if a.button("Anterior", key="guide_prev", disabled=index == 0, use_container_width=True):
            st.session_state["guide_step"] = index - 1
            st.rerun()
        if b.button("Próximo" if index < 4 else "Rever início", key="guide_next", use_container_width=True):
            st.session_state["guide_step"] = (index + 1) % 5
            st.session_state["guide_animate"] = True
            st.rerun()
        from solem_ui import navigate
        st.button(f"Abrir {destination}", key="guide_open", on_click=navigate, args=(destination,))
        if not st.session_state.get("generic_account"):
            st.caption("Seu menu também reúne Estudos, Biblioteca, Financeiro, Publicações e Ideias e roteiros. Você pode explorar cada área no seu tempo.")
        if not prefs.get("guide_done", False) and st.button("Concluir guia / ver depois", key="guide_done"):
            save_preferences(guide_done=True)
        st.caption("Guia opcional. Você pode reabrir esta caixa quando quiser.")


def weekly_insight(records, today):
    rows = workout_week(records, today)
    active = sum(r["sessions"] > 0 for r in rows)
    with st.container(key="experience_week"):
        st.subheader("Seu ritmo nos últimos 7 dias")
        st.caption(f"{active} dias com treino · {sum(r['sessions'] for r in rows)} sessões registradas. Descanso não remove XP.")
        import plotly.graph_objects as go
        chart = go.Figure(go.Bar(x=[r["date"].strftime("%d/%m") for r in rows], y=[r["sessions"] for r in rows],
                                marker_color="#83dcff", text=[str(r["sessions"]) for r in rows], textposition="outside",
                                hovertemplate="%{x}: %{y} sessões<extra></extra>"))
        chart.update_layout(height=220, margin=dict(t=25, b=25, l=20, r=20), yaxis=dict(title="Sessões", dtick=1, range=[0, max(1, max(r["sessions"] for r in rows)) + 0.5]), showlegend=False)
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False, "staticPlot": True}, key="experience_chart")
        with st.expander("Ver os valores do gráfico"):
            st.dataframe([{"Dia":r["date"].strftime("%d/%m"), "Sessões":r["sessions"], "Repetições":r["reps"], "Distância (km)":round(r["km"], 2)} for r in rows], hide_index=True, use_container_width=True)
        if not active:
            st.info("Seu gráfico começa com o primeiro treino salvo. Abra Treino e registre uma atividade para acompanhar sua evolução.")


def workout_media():
    with st.expander("Minha trilha de treino · músicas e clipes"):
        st.write("Escolha o que acompanha seu treino. A reprodução só começa quando você apertar play.")
        st.caption("Arquivos ficam apenas nesta sessão do site; links favoritos são privados da sua conta. Ao sair desta aba, a reprodução para. Clipes externos podem ter flashes: prefira áudio se isso causar desconforto.")
        upload = st.file_uploader("Áudio ou vídeo do seu dispositivo · até 30 MB", type=["mp3", "m4a", "wav", "ogg", "mp4", "webm"], key="training_media_file", max_upload_size=30)
        if upload is not None:
            if upload.size > 30 * 1024 * 1024:
                st.error("Escolha um arquivo de até 30 MB.")
            elif upload.name.lower().endswith((".mp4", ".webm")):
                st.video(upload, autoplay=False)
            else:
                st.audio(upload, autoplay=False)
        prefs = st.session_state.get("journey_preferences", {})
        links = prefs.get("media", [])
        if links:
            selected = st.selectbox("Meus favoritos", range(len(links)), format_func=lambda i: links[i]["title"], key="training_media_selection")
            item = links[selected]
            st.link_button("Abrir no serviço de música ou vídeo ↗", item["url"])
            if st.button("Remover este favorito", key="media_remove"):
                save_preferences(media=[r for i, r in enumerate(links) if i != selected])
        with st.form("media_link_form", clear_on_submit=True):
            title = st.text_input("Nome da música, clipe ou playlist", max_chars=80)
            url = st.text_input("Link do YouTube, Spotify ou SoundCloud", max_chars=500)
            submitted = st.form_submit_button("Guardar favorito", disabled=len(links) >= 8)
        if submitted:
            try:
                item = media_link(title, url)
                if any(r["url"] == item["url"] for r in links):
                    st.info("Este link já está nos seus favoritos.")
                else:
                    save_preferences(media=links + [item])
            except ValueError as error:
                st.error(str(error))
        st.caption("Até 8 favoritos. Os serviços externos podem exigir conta; nenhum plano pago novo é necessário para guardar links ou tocar seus arquivos.")
