from copy import deepcopy
from streamlit.testing.v1 import AppTest
from solem_navigation import menu_tabs, visible_menu
from solem_ui import PAGES


def test_legacy_dashboard_preferences_keep_parent_visible_without_mutation():
    saved = ["physical", "study_progress", "languages"]
    before = saved.copy()
    visible = visible_menu(PAGES, {"menu_tabs": saved})
    assert "Treino" in visible and "Estudar" in visible
    assert "Evolução física" not in visible and "Evolução nos estudos" not in visible
    assert saved == before
    assert "training" not in menu_tabs([])


def test_modules_show_dashboards_without_changing_records(monkeypatch):
    monkeypatch.setenv("SOLEM_DEMO", "1")
    app = AppTest.from_file("app.py", default_timeout=40).run()
    before = deepcopy(app.session_state.solem_demo_records)
    for parent, dashboard, chart_key in [("Treino", "Evolução física", "filtro_tempo_dash_fisico"),
                                         ("Estudar", "Evolução nos estudos", "filtro_tempo_dash_estudos")]:
        assert dashboard not in app.radio(key="solem_page").options
        app.radio(key="solem_page").set_value(parent).run()
        assert not app.exception
        app.radio(key=f"module_section_{parent}").set_value(dashboard).run()
        assert not app.exception
        assert app.radio(key="solem_page").value == parent
        assert app.selectbox(key=chart_key)
        app.radio(key=f"module_section_{parent}").set_value("Registrar").run()
        assert not app.exception
    assert app.session_state.solem_demo_records == before
