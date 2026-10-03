import pytest
from solem_workout_timer import apply_timing_event, duration_minutes


def test_integer_minutes_round_up_and_reject_invalid_values():
    assert [duration_minutes(s) for s in (0, 1, 60, 61, 125)] == [0, 1, 1, 2, 3]
    for value in (-1, float("nan"), float("inf"), 86401):
        with pytest.raises(ValueError):
            duration_minutes(value)


def test_gps_transfers_time_and_distance_once_without_overwriting_manual_edit():
    state = {}
    event = dict(event="finished", id="gps-1", km=2.125, duration_seconds=125)
    apply_timing_event(state, "Caminhada", ("duracao_min", "distancia_km"), event, "gps")
    assert state["treino_duracao_min_Caminhada"] == 3
    assert state["treino_distancia"] == 2.125
    assert state["treino_tempo_medido_Caminhada"]["seconds"] == 125
    state["treino_duracao_min_Caminhada"] = 4
    apply_timing_event(state, "Caminhada", ("duracao_min", "distancia_km"), event, "gps")
    assert state["treino_duracao_min_Caminhada"] == 4
    assert "treino_duracao_min_Corrida" not in state


def test_countdown_configures_rest_and_stopwatch_transfers_isometry():
    state = {}
    apply_timing_event(state, "Agachamento", ("descanso_seg",),
                       dict(event="configure", id="rest-1", seconds=90), "timer")
    assert state["treino_descanso_seg_Agachamento"] == 90
    apply_timing_event(state, "Prancha", ("isometria_segundos", "repeticoes"),
                       dict(event="use_time", id="watch-1", duration_seconds=42), "timer")
    assert state["treino_isometria_segundos_Prancha"] == 42
    assert "treino_duracao_min_Prancha" not in state


def test_invalid_gps_event_does_not_partially_change_form():
    state = {}
    apply_timing_event(state, "Corrida", ("duracao_min", "distancia_km"),
                       dict(event="finished", id="bad", km=float("nan"), duration_seconds=60), "gps")
    assert state == {}
