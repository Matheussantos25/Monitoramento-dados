"""Workout clocks and validated transfer to the existing training fields."""
import math
from pathlib import Path
import streamlit.components.v1 as components

_timer = components.declare_component(
    "solem_workout_timer", path=str(Path(__file__).resolve().parent / "assets" / "workout_timer"))


def workout_timer(exercise, rest_seconds, can_apply, has_rest):
    return _timer(exercise=exercise, rest_seconds=rest_seconds, can_apply=can_apply,
                  has_rest=has_rest, key=f"workout_clock_{exercise}", default=None)


def duration_minutes(seconds):
    """The existing integer-minute column rounds up; keep exact seconds separately."""
    value = float(seconds)
    if not math.isfinite(value) or not 0 <= value <= 86400:
        raise ValueError("Tempo inválido")
    return math.ceil(value / 60)


def apply_timing_event(state, exercise, fields, event, source):
    if not isinstance(event, dict) or not isinstance(event.get("id"), str):
        return
    event_key = f"workout_clock_event_{source}_{exercise}"
    if state.get(event_key) == event["id"]:
        return
    try:
        if event.get("event") == "configure" and source == "timer" and "descanso_seg" in fields:
            seconds = int(event["seconds"])
            if not 0 <= seconds <= 86400:
                return
            state[f"treino_descanso_seg_{exercise}"] = seconds
        elif event.get("event") in ("finished", "use_time"):
            seconds = int(event["duration_seconds"])
            minutes = duration_minutes(seconds)
            km = float(event["km"]) if source == "gps" else None
            if km is not None and (not math.isfinite(km) or not 0 <= km <= 1000):
                return
            if "duracao_min" in fields:
                state[f"treino_duracao_min_{exercise}"] = minutes
                state[f"treino_tempo_medido_{exercise}"] = {"seconds": seconds, "minutes": minutes, "source": source}
            elif "isometria_segundos" in fields:
                state[f"treino_isometria_segundos_{exercise}"] = seconds
            if km is not None:
                state["treino_distancia"] = round(km, 3)
        else:
            return
    except (ValueError, TypeError, KeyError, OverflowError):
        return
    state[event_key] = event["id"]
    return True
