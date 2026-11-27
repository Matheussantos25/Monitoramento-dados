import streamlit as st
from solem_navigation import TABS, PINNED, menu_tabs


def menu_editor(key="menu_preferences", onboarding=False):
    from solem_ui import PAGES
    from solem_experience_ui import save_preferences
    prefs = st.session_state.get("journey_preferences", {})
    if st.session_state.get("journey_data") is None:
        st.info("Conecte-se novamente para carregar e personalizar suas abas.")
        return
    current = menu_tabs(prefs.get("menu_tabs"), st.session_state.get("generic_account", False))
    offered = [k for k, label in TABS.items() if label in PAGES and k not in PINNED]
    st.subheader("O que você quer acompanhar?" if onboarding else "Minhas abas")
    st.caption("Escolha as áreas do seu menu. Ocultar uma aba mantém todos os registros. Você pode mudar depois em Metas e aparência → Minhas abas.")
    with st.form(key):
        selected = st.multiselect("Abas do meu menu", offered, default=[k for k in offered if k in current],
                                  format_func=lambda k: TABS[k], key=key+"_tabs")
        st.caption("Visão geral, Metas e aparência e Configurações ficam sempre acessíveis.")
        submitted = st.form_submit_button("Começar com estas abas" if onboarding else "Salvar minhas abas")
    if submitted:
        # The APK-only selections survive a web edit (and vice versa).
        values = selected + [k for k in current if k not in offered]
        save_preferences(menu_tabs=menu_tabs(values), menu_done=True)


def menu_welcome():
    prefs = st.session_state.get("journey_preferences", {})
    if (st.session_state.get("generic_account") and not prefs.get("menu_done")
            and st.session_state.get("journey_data") is not None
            and not st.session_state.get("menu_welcome_later")):
        with st.expander("Bem-vindo · monte seu menu", expanded=True):
            menu_editor("menu_welcome", onboarding=True)
            if st.button("Escolher depois", key="menu_later"):
                st.session_state["menu_welcome_later"] = True
                st.rerun()


PAGE_ICONS = {
    "Visão geral": "home", "Treino": "fitness_center", "Evolução física": "monitoring",
    "Saúde": "favorite", "Estudar": "school", "Evolução nos estudos": "query_stats",
    "Idiomas": "translate", "Prompts": "terminal", "Anotações": "edit_note",
    "Resumos": "summarize", "PDFs": "picture_as_pdf", "Mapas mentais": "account_tree",
    "Cronograma": "calendar_month", "Financeiro": "account_balance_wallet",
    "Publicações": "video_library", "Ideias e roteiros": "movie_edit",
    "Metas e aparência": "tune", "Configurações": "settings",
}


def navigation(available, progress, navigate, on_logout):
    from pathlib import Path
    available = [page for page in PAGE_ICONS if page in available]
    compact = st.session_state.get("navigation_compact", False)
    css = (Path(__file__).parent / "assets" / "navigation.css").read_text(encoding="utf-8")
    # Keep native radio keyboard behavior and stable page values for existing callers.
    for index, page in enumerate(available, 1):
        css += f'.st-key-solem_page [role="radiogroup"] label:nth-child({index})::before{{content:"{PAGE_ICONS[page]}" / "";}}'
    st.html("<style>" + css + "</style>")
    with st.sidebar:
        st.html('<div class="solem-navigation' + (' compact' if compact else '') + '"></div>')
        st.html('<div class="sidebar-brand">✳ <b>solem</b><small>CORPO & MENTE</small></div>')
        st.toggle("Somente ícones", key="navigation_compact")
        page = st.radio("Navegação principal", available, key="solem_page", label_visibility="collapsed")
        st.caption(f"Nível {progress['level']} · {progress['xp']} XP")
        st.button("Personalizar abas", icon=":material/tune:", on_click=navigate,
                  args=("Metas e aparência",), key="menu_customize", help="Escolher quais abas aparecem")
        if on_logout:
            st.button("Sair", icon=":material/logout:", on_click=on_logout,
                      key="solem_logout", help="Sair da conta", use_container_width=True)
    with st.container(key="mobile_navigation"):
        shortcuts = [p for p in ("Visão geral", "Treino", "Saúde", "Idiomas") if p in available]
        with st.container(key="mobile_navigation_items", horizontal=True):
            for destination in shortcuts:
                label = "Início" if destination == "Visão geral" else destination
                st.button(label, icon=f":material/{PAGE_ICONS[destination]}:",
                          key=f"mobile_nav_{destination}", help=destination,
                          type="primary" if destination == page else "secondary",
                          on_click=navigate, args=(destination,))
            with st.popover("Abas", icon=":material/apps:", help="Todas as suas abas"), st.container(key="mobile_all_tabs"):
                st.markdown("**Suas abas**")
                for destination in available:
                    st.button(destination, icon=f":material/{PAGE_ICONS[destination]}:",
                              key=f"mobile_all_{destination}",
                              type="primary" if destination == page else "secondary",
                              on_click=navigate, args=(destination,), use_container_width=True)
                if on_logout:
                    st.button("Sair", icon=":material/logout:", on_click=on_logout, key="mobile_logout")
        if page not in shortcuts:
            st.caption(page)
    return page


def module_section(page):
    """Internal module navigation; only the selected view renders its widgets."""
    dashboards = {"Treino": "Evolução física", "Estudar": "Evolução nos estudos"}
    if page not in dashboards:
        return page
    with st.container(key="module_navigation"):
        st.markdown(f"### {page}")
        selected = st.radio(f"Seção de {page}", ["Registrar", dashboards[page]],
                           horizontal=True, key=f"module_section_{page}", label_visibility="collapsed")
    return page if selected == "Registrar" else dashboards[page]
