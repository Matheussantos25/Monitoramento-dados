from copy import deepcopy
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from solem_health import optional_workout_load, workout_load


def test_load_modes_validate_only_added_weight():
    for exercise in ("Flexão", "Agachamento", "Barra Fixa (Pronada)", "Prancha"):
        assert optional_workout_load(exercise)
        assert workout_load(exercise, False, 20) == 0
        assert workout_load(exercise, True, 7.5) == 7.5
        for bad in (0, -1, float("nan"), float("inf")):
            with pytest.raises(ValueError): workout_load(exercise, True, bad)
    assert not optional_workout_load("Corrida")
    assert not optional_workout_load("Puxada Alta")
    assert workout_load("Puxada Alta", True, 30) == 30


def test_web_form_hides_normal_load_and_preserves_history(monkeypatch):
    monkeypatch.setenv("SOLEM_DEMO", "1")
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),default_timeout=40).run()
    original=deepcopy(app.session_state.solem_demo_records)
    app.radio(key="solem_page").set_value("Treino").run()
    app.selectbox(key="treino_exercicio").set_value("Flexão").run()
    mode="treino_tipo_carga_Flexão"
    assert app.radio(key=mode).value == "Normal (sem peso extra)"
    assert not any(w.label=="Peso extra (kg)" for w in app.number_input)
    app.radio(key=mode).set_value("Com peso").run()
    app.number_input(key="treino_repeticoes_Flexão").set_value(10)
    app.button(key="FormSubmitter:registro_treino-Salvar treino").click().run()
    assert len(app.session_state.solem_demo_records)==len(original)
    assert app.error
    app.number_input(key="treino_carga_kg_Flexão").set_value(7.5)
    app.number_input(key="treino_repeticoes_Flexão").set_value(10)
    app.button(key="FormSubmitter:registro_treino-Salvar treino").click().run()
    assert not app.exception
    assert app.session_state.solem_demo_records[-1]["carga_kg"]==7.5
    app.number_input(key="treino_carga_kg_Flexão").set_value(12).run()
    app.radio(key=mode).set_value("Normal (sem peso extra)").run()
    app.number_input(key="treino_repeticoes_Flexão").set_value(10)
    app.button(key="FormSubmitter:registro_treino-Salvar treino").click().run()
    assert not app.exception
    assert app.session_state.solem_demo_records[-1]["carga_kg"]==0
    assert app.session_state.solem_demo_records[:len(original)]==original
