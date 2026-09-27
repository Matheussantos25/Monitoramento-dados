"""Accessible, read-only calendar; day details stay inside the user's browser."""
from pathlib import Path
import streamlit.components.v1 as components


_calendar = components.declare_component(
    "solem_journal_calendar",
    path=str(Path(__file__).resolve().parent / "assets" / "journal_calendar"),
)


def journal_calendar(year, month, today, days):
    _calendar(year=year, month=month, today=today.isoformat(), days=days,
              key=f"journal_calendar_{year}_{month}", default=None)
