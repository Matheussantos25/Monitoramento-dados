"""Read-only, local technique illustrations. Never writes workout state."""
import json
from pathlib import Path

import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
_component = components.declare_component(
    "solem_exercise_guide", path=str(ROOT / "assets" / "exercise_guide"))


def guide_catalog():
    return json.loads((ROOT / "assets" / "exercise_guides.json").read_text(encoding="utf8"))


def guide_payload(exercise):
    data = guide_catalog()
    guide = data["guides"].get(exercise, {
        "motion": "", "view": "Guia ainda não disponível", "grip": "",
        "labels": [], "cues": ["Este exercício não tem uma técnica ilustrada definida. Seu registro continua disponível."],
        "avoid": "Confirme a execução com um profissional.", "source": ""})
    return dict(exercise=exercise, guide=guide, motion=data["motions"].get(guide["motion"]),
                grip=data["grips"].get(guide["grip"]), notice=data["notice"])


def exercise_guide(exercise):
    return _component(**guide_payload(exercise), key=f"technique_{exercise}", default=None)
