"""Private per-user health diary; never use the legacy public treinos client here."""
from uuid import uuid4

import streamlit as st


def list_entries(client, demo=False):
    if demo:
        return st.session_state.setdefault("demo_health_entries", [])
    client.auth.get_user()
    rows = []
    while True:
        page = client.table("solem_health_entries").select(
            "id,day,logged_at,kind,details,created_at").order(
            "day", desc=True).order("logged_at", desc=True).range(
            len(rows), len(rows) + 499).execute().data
        rows.extend(page)
        if len(page) < 500:
            return rows


def save_entry(client, entry, old=None, demo=False):
    if demo:
        rows = st.session_state.setdefault("demo_health_entries", [])
        if old:
            old.update(entry)
        else:
            rows.append({"id": str(uuid4()), **entry})
        return
    if old:
        client.table("solem_health_entries").update(entry).eq("id", old["id"]).execute()
    else:
        client.table("solem_health_entries").insert(entry).execute()


def delete_entry(client, entry_id, demo=False):
    if demo:
        st.session_state["demo_health_entries"] = [
            row for row in st.session_state.get("demo_health_entries", []) if row["id"] != entry_id]
        return
    client.table("solem_health_entries").delete().eq("id", entry_id).execute()

