import os
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_personal_settings_save_and_checkup_navigation():
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "personal"}):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        assert not app.exception
        assert not any(x.key in ("checkup_go_questions", "checkup_go_study") for x in app.button)
        app.button(key="journey_customize").click().run()
        assert app.number_input(key="target_agachamento").value == 100
        assert app.number_input(key="target_flexao").value == 100
        app.number_input(key="target_flexao").set_value(120)
        next(b for b in app.button if b.label == "Salvar minhas metas").click().run()
        assert not app.exception
        app.radio(key="solem_page").set_value("Visão geral").run()
        assert app.session_state["journey_preferences"]["targets"]["flexao"] == 120
        app.button(key="checkup_go_created").click().run()
        assert app.radio(key="solem_page").value == "Criador"
        assert not app.exception
        assert any("Canal principal" in s.value for s in app.subheader)


def test_creator_video_dialog_save_edit_trash_restore():
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "personal"}):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        app.radio(key="solem_page").set_value("Criador").run()
        app.button(key="creator_new_video").click().run()
        next(i for i in app.text_input if i.label == "Título ou ideia do vídeo").set_value("Meu vídeo de teste").run()
        app.selectbox(key="video_stage_new").set_value("Pronto").run()
        assert next(i for i in app.text_input if i.label == "Título ou ideia do vídeo").value == "Meu vídeo de teste"
        next(b for b in app.button if b.label == "Salvar vídeo").click().run()
        assert not app.exception
        row = next(r for r in app.session_state["journey_data"]["items"] if r["kind"] == "video")
        assert row["stage"] == "Pronto"
        app.button(key=f"video_edit_{row['id']}").click().run()
        app.selectbox(key=f"video_stage_{row['id']}").set_value("Publicado").run()
        next(b for b in app.button if b.label == "Salvar vídeo").click().run()
        assert not app.exception
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "1 / 2"
        app.button(key="creator_new_video").click().run()
        app.selectbox(key="video_stage_new").set_value("Publicado").run()
        next(i for i in app.text_input if i.label == "Título ou ideia do vídeo").set_value("Segundo vídeo")
        next(b for b in app.button if b.label == "Salvar vídeo").click().run()
        assert not app.exception
        assert app.session_state["creator_rank_high_water"] == 1
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "2 / 2"
        # Keep the existing archive/restore assertions scoped to the first item.
        second = next(r for r in app.session_state["journey_data"]["items"] if r["kind"] == "video" and r["id"] != row["id"])
        app.button(key=f"video_archive_{second['id']}").click().run()
        app.button(key=f"video_archive_{row['id']}").click().run()
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "0 / 2"
        app.button(key=f"creator_restore_{row['id']}").click().run()
        assert not app.exception
        assert next(m for m in app.metric if m.label == "Publicados hoje").value == "1 / 2"


def test_failed_load_preserves_history_and_exposes_retry_without_zero_creator_counts():
    with patch.dict(os.environ, {"SOLEM_DEMO": "1", "SOLEM_DEMO_PROFILE": "personal"}), patch("solem_journey.JourneyStore.load", side_effect=RuntimeError("offline")):
        app = AppTest.from_file(str(APP), default_timeout=40).run()
        assert not app.exception
        assert app.session_state["journey_data"] is None
        assert app.session_state["solem_demo_records"]
        app.radio(key="solem_page").set_value("Metas e aparência").run()
        assert app.button(key="journey_retry")
        assert not any(b.label == "Salvar minhas metas" for b in app.button)
