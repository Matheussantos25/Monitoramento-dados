"""Deployment regression: a warm Cloud process can retain the old renderer."""
from datetime import date
from unittest.mock import patch


def test_workout_calendar_survives_legacy_journal_renderer():
    import solem_journal_component
    import solem_training_plan_ui

    def legacy_calendar(year, month, today, days):
        return solem_journal_component._calendar(
            year=year, month=month, today=today.isoformat(), days=days,
            key=f"journal_calendar_{year}_{month}", default=None)

    # Reproduce the already-imported four-argument renderer in the traceback.
    with patch.object(solem_training_plan_ui, "journal_calendar", legacy_calendar, create=True), \
         patch.object(solem_journal_component, "journal_calendar", legacy_calendar), \
         patch.object(solem_journal_component, "_calendar") as render:
        solem_training_plan_ui.workout_calendar([], date(2026, 10, 19))
        legacy_calendar(2026, 10, date(2026, 10, 19), [])
    keys = [call.kwargs["key"] for call in render.call_args_list]
    assert keys == ["workout_calendar_2026_10", "journal_calendar_2026_10"]
    assert len(render.call_args_list[0].kwargs["days"]) == 31


def test_overview_and_training_render_with_legacy_module(monkeypatch):
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    import solem_journal_component

    def legacy_calendar(year, month, today, days):
        return solem_journal_component._calendar(
            year=year, month=month, today=today.isoformat(), days=days,
            key=f"journal_calendar_{year}_{month}", default=None)

    monkeypatch.setenv("SOLEM_DEMO", "1")
    monkeypatch.setenv("SOLEM_DEMO_PROFILE", "personal")
    monkeypatch.setattr(solem_journal_component, "journal_calendar", legacy_calendar)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"),
                           default_timeout=40).run()
    assert not app.exception
    assert app.number_input(key="workout_calendar_year").value >= 2026
    app.selectbox(key="workout_calendar_month").set_value(9).run()
    assert not app.exception
    app.radio(key="solem_page").set_value("Treino").run()
    assert not app.exception
    assert not any(w.key == "workout_calendar_year" for w in app.number_input)
    assert not any(e.label == "Plano semanal e calendário de treino" for e in app.expander)
    assert app.selectbox(key="treino_exercicio") is not None
    app.radio(key="solem_page").set_value("Visão geral").run()
    assert not app.exception
    assert app.number_input(key="workout_calendar_year") is not None
