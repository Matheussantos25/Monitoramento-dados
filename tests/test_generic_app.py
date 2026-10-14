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
        assert not {"checkup_go_mewing", "checkup_go_study", "checkup_go_questions", "checkup_go_published"} & {x.key for x in app.button}
        assert app.radio(key="solem_page").options == ["Visão geral", "Treino", "Evolução física", "Saúde", "Metas e aparência", "Configurações"]
        for page in app.radio(key="solem_page").options:
            app.radio(key="solem_page").set_value(page).run()
            assert not app.exception, [e.message for e in app.exception]
        app.radio(key="solem_page").set_value("Treino").run()
        assert set(app.selectbox(key="treino_exercicio").options) == {"Agachamento", "Flexão", "Caminhada", "Corrida"}
        app.selectbox(key="treino_exercicio").set_value("Agachamento").run()
        next(x for x in app.number_input if x.label == "Repetições (Total)").set_value(15)
        next(x for x in app.button if x.label == "Salvar treino").click().run()
        assert not app.exception
        assert len(app.session_state["solem_demo_records"]) == 1
        assert app.session_state["solem_demo_records"][0]["exercicio"] == "Agachamento"
        restored = AppTest.from_file(str(APP), default_timeout=30)
        restored.session_state["solem_page"] = "Publicações"
        restored.run()
        assert not restored.exception
        assert restored.radio(key="solem_page").value == "Visão geral"
