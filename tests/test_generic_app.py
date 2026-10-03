import os
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_new_account_empty_pages_generic_presets_and_save():
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "generic"}):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        assert not app.exception
        assert app.session_state["solem_demo_records"] == []
        assert not any(x.key == "checkup_go_mewing" for x in app.button)
        for page in app.radio(key="solem_page").options:
            app.radio(key="solem_page").set_value(page).run()
            assert not app.exception, [e.message for e in app.exception]
        app.radio(key="solem_page").set_value("Treino").run()
        assert "Mewing com borracha" not in app.selectbox(key="treino_exercicio").options
        assert "Massagem Facial" not in app.selectbox(key="treino_exercicio").options
        app.selectbox(key="treino_exercicio").set_value("Agachamento").run()
        next(x for x in app.number_input if x.label == "Repetições (Total)").set_value(15)
        next(x for x in app.button if x.label == "Salvar treino").click().run()
        assert not app.exception
        assert len(app.session_state["solem_demo_records"]) == 1
        app.radio(key="solem_page").set_value("Estudar").run()
        assert "Programação" in app.selectbox(key="disciplina_estudo_select").options
        assert not any("FGV" in str(x.value) for x in app.markdown)
        assert not app.get("help")  # No DeltaGenerator accidentally rendered by Streamlit magic.
        next(x for x in app.number_input if x.label == "Tempo de Vídeo Aula (min)").set_value(25)
        next(x for x in app.button if "Salvar" in x.label and "sessão" in x.label.lower()).click().run()
        assert not app.exception
        app.radio(key="solem_page").set_value("Evolução nos estudos").run()
        assert not app.exception
        assert not any("Edital Completo" in x.label for x in app.expander)
        app.radio(key="solem_page").set_value("Prompts").run()
        assert not app.exception
        assert "Praticar programação" in app.selectbox(key="seletor_prompt_estudo").options
        app.radio(key="solem_page").set_value("Estudar").run()
        next(x for x in app.radio if x.label == "Tipo de Sessão").set_value("📚 Leitura / Prática").run()
        next(x for x in app.number_input if x.label == "Tempo de leitura ou prática (min)").set_value(30)
        next(x for x in app.button if x.label == "Salvar sessão").click().run()
        assert not app.exception
        record = app.session_state["solem_demo_records"][-1]
        app.button(key=f"manage_edit_Estudar_{record['id']}").click().run()
        assert not app.exception
        app.number_input(key=f"reading_edit_duration_{record['id']}").set_value(35)
        next(x for x in app.button if "Salvar Alterações" in x.label).click().run()
        assert not app.exception
        assert app.session_state["solem_demo_records"][-1]["duracao_min"] == 35
