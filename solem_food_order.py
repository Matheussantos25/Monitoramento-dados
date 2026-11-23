"""Draft-only food ordering. Scale readings belong to chronological slots."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

_sorter = components.declare_component(
    "solem_food_order", path=str(Path(__file__).parent / "assets" / "food_order"))


def apply_order_event(state, key, event):
    order = state.get(f"{key}_order", [])
    revision = state.get(f"{key}_order_revision", 0)
    if not isinstance(event, dict) or event.get("revision") != revision or event.get("base") != order:
        return False
    proposed = event.get("order")
    if (not isinstance(proposed, list) or not all(isinstance(x, str) for x in proposed)
            or len(proposed) != len(order) or len(set(proposed)) != len(order)
            or set(proposed) != set(order) or proposed == order):
        return False
    state[f"{key}_order"] = proposed
    if f"{key}_added" in state:
        state[f"{key}_added"] = [token.removeprefix("added:") for token in proposed if token.startswith("added:")]
    state[f"{key}_order_revision"] = revision + 1
    state[f"{key}_confirmed"] = False
    return True


def sync_order(state, key, available, defaults):
    """Keep intentional moves; additions append, removals invalidate affected readings."""
    old = state.get(f"{key}_order")
    order = list(available) if old is None else [x for x in old if x in available] + [x for x in available if x not in old]
    if old is not None and order != old:
        first = next((i for i, (a, b) in enumerate(zip(old, order)) if a != b), min(len(old), len(order)))
        for i in range(first, max(len(order), len(old))):
            state[f"{key}_slot_reading_{i}"] = 0.0
        state[f"{key}_confirmed"] = False
    if old != order:
        state[f"{key}_order"] = order
        state[f"{key}_order_revision"] = state.get(f"{key}_order_revision", 0) + 1
    for i, token in enumerate(order):
        state.setdefault(f"{key}_slot_reading_{i}", float(defaults.get(token, 0)))
    return order


def food_order(key, labels):
    order = st.session_state[f"{key}_order"]
    if len(order) < 2:
        return
    st.markdown("**Ordem dos alimentos**")
    st.caption("Arraste pela alça ⋮⋮ ou use as setas. As leituras ficam na mesma posição; confira os novos pesos antes de salvar.")
    component_key = f"{key}_sorter"

    def changed():
        apply_order_event(st.session_state, key, st.session_state.get(component_key))

    _sorter(items=[dict(id=token, label=labels[token]) for token in order],
            revision=st.session_state.get(f"{key}_order_revision", 0),
            key=component_key, on_change=changed, default=None)
