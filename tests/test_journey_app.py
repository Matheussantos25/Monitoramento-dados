import os
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_personal_settings_save_and_checkup_navigation():
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "personal"}):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        assert not app.exception
        assert not any(x.key in ("checkup_go_questions", "checkup_go_study", "checkup_go_created") for x in app.button)
        assert any(c.label == "Vídeo 1 publicado" for c in app.checkbox)
        app.button(key="journey_customize").click().run()
        assert app.number_input(key="target_agachamento").value == 100
        assert app.number_input(key="target_flexao").value == 100
        assert not any(n.key == "target_created" for n in app.number_input)
        app.number_input(key="target_flexao").set_value(120)
        next(b for b in app.button if b.label == "Salvar minhas metas").click().run()
        assert not app.exception
        app.radio(key="solem_page").set_value("Visão geral").run()
        assert app.session_state["journey_preferences"]["targets"]["flexao"] == 120
        app.button(key="journey_open_creator").click().run()
        assert app.radio(key="solem_page").value == "Publicações"
        assert not app.exception


def test_post_checklist_edit_uncheck_restore_and_no_duplicate_on_rerun():
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "personal"}):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        next(c for c in app.checkbox if c.label == "Vídeo 1 publicado").check().run()
        assert not app.exception
        row = next(r for r in app.session_state["journey_data"]["items"] if r["kind"] == "video")
        assert row["stage"] == "Publicado" and row["produced_on"] == row["published_on"]
        app.run()
        assert len([r for r in app.session_state["journey_data"]["items"] if r["kind"] == "video"]) == 1
        app.radio(key="solem_page").set_value("Publicações").run()
        assert not any(s.label == "Etapa de produção" for s in app.selectbox)
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "1 / 2"
        app.button(key=f"video_edit_{row['id']}").click().run()
        next(i for i in app.text_input if i.label == "Título (opcional)").set_value("Publicação revisada")
        next(b for b in app.button if b.label == "Salvar publicação").click().run()
        assert not app.exception
        next(c for c in app.checkbox if c.label == "Vídeo 2 publicado").check().run()
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "2 / 2"
        next(c for c in app.checkbox if c.key.startswith(f"daily_posts_{row['id']}_")).uncheck().run()
        assert not app.exception
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "1 / 2"
        app.button(key=f"creator_restore_{row['id']}").click().run()
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "2 / 2"
        assert not app.exception
        app.radio(key="solem_page").set_value("Visão geral").run()
        assert len([r for r in app.session_state["journey_data"]["items"] if r["kind"] == "video"]) == 2


def test_failed_load_preserves_history_and_exposes_retry_without_zero_creator_counts():
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "personal"}), patch("solem_journey.JourneyStore.load", side_effect=RuntimeError("offline")):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        assert not app.exception
        assert app.session_state["journey_data"] is None
        assert app.session_state["solem_demo_records"]
        app.radio(key="solem_page").set_value("Metas e aparência").run()
        assert app.button(key="journey_retry")
        assert not any(b.label == "Salvar minhas metas" for b in app.button)
