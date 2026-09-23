"""Opt-in browser distance tracker for walking and running.

Only the final distance crosses the component boundary; GPS coordinates stay
inside the browser iframe and are never sent to Streamlit or Supabase.
"""
from pathlib import Path

import streamlit.components.v1 as components


_tracker = components.declare_component(
    "solem_gps_tracker", path=str(Path(__file__).resolve().parent / "assets" / "gps_tracker"))


def gps_distance_tracker(key="gps_treino_web"):
    return _tracker(key=key, default=None)
