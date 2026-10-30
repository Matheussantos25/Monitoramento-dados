from copy import deepcopy
from datetime import date
import os
from unittest.mock import patch
import pytest
from streamlit.testing.v1 import AppTest
from solem_experience import media_link, workout_week
from solem_journey import preferences, JourneyStore


@pytest.mark.parametrize("url", ["javascript:alert(1)", "http://youtube.com/watch?v=x", "https://youtube.com.evil.test/", "https://user:pass@youtube.com/", "https://127.0.0.1/", "https://youtube.com:123/", "https://youtube.com/\n"])
def test_links_reject_untrusted_destinations(url):
    # Trailing whitespace is intentionally trimmed; embedded control characters are rejected.
    if url.endswith("\n"):
        url = "https://youtube.com/\nx"
    with pytest.raises(ValueError):
        media_link("Minha playlist", url)


def test_preferences_backwards_compatible_and_account_isolated():
    old=preferences(personal=True)
    old.pop("media");old.pop("comfort");old.pop("contrast");old.pop("large_text");old.pop("guide_done")
    original=deepcopy(old)
    new=preferences(old,personal=True)
    new.update(comfort=True,media=[media_link("Foco","https://open.spotify.com/playlist/example")])
    state={};a=JourneyStore(demo_state=state,demo_owner="a");b=JourneyStore(demo_state=state,demo_owner="b")
    a.save_settings(new)
    assert b.load()["settings"] is None
    assert a.load()["settings"]["preferences"]["targets"]==old["targets"]
    assert old==original


def test_rhythm_deduplicates_and_excludes_future_empty_and_study():
    rows=[dict(id=1,data="2026-10-30",grupo_muscular="Pernas",repeticoes=20),
          dict(id=2,data="2026-10-29",grupo_muscular="Cardio",distancia_km=2),
          dict(id=3,data="2026-10-31",grupo_muscular="Pernas",repeticoes=90),
          dict(id=4,data="2026-10-30",grupo_muscular="Pernas",repeticoes=0),
          dict(id=5,data="2026-10-30",grupo_muscular="Estudos",repeticoes=30)]
    rows.append(rows[0]);original=deepcopy(rows)
    days=workout_week(rows,date(2026,10,30))
    assert len(days)==7 and sum(r["sessions"] for r in days)==2
    assert days[-1]["reps"]==20 and days[-2]["km"]==2
    assert rows==original


def test_new_account_guide_preferences_and_media_flow_without_history_changes():
    with patch.dict(os.environ,{"SOLEM_DEMO":"1","SOLEM_DEMO_PROFILE":"generic"}):
        app=AppTest.from_file("app.py",default_timeout=40).run()
        assert not app.exception
        initial=deepcopy(app.session_state["solem_demo_records"])
        assert not any(b.key=="journey_open_creator" for b in app.button)
        app.button(key="guide_next").click().run()
        assert app.session_state["guide_step"]==1
        app.button(key="guide_done").click().run()
        assert app.session_state["journey_preferences"]["guide_done"]
        app.radio(key="solem_page").set_value("Metas e aparência").run()
        next(c for c in app.checkbox if c.label.startswith("Modo tranquilo")).check()
        next(c for c in app.checkbox if c.label=="Texto maior").check()
        next(b for b in app.button if b.label=="Salvar minhas metas").click().run()
        assert app.session_state["journey_preferences"]["comfort"]
        app.radio(key="solem_page").set_value("Treino").run()
        next(t for t in app.text_input if t.label=="Nome da música, clipe ou playlist").set_value("Minha playlist")
        next(t for t in app.text_input if t.label.startswith("Link do YouTube")).set_value("https://open.spotify.com/playlist/example")
        next(b for b in app.button if b.label=="Guardar favorito").click().run()
        assert not app.exception
        assert len(app.session_state["journey_preferences"]["media"])==1
        app.run()
        assert len(app.session_state["journey_preferences"]["media"])==1
        app.button(key="media_remove").click().run()
        assert not app.session_state["journey_preferences"]["media"]
        assert app.session_state["solem_demo_records"]==initial
