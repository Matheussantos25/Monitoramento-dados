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
