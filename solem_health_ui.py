"""Authenticated health diary. New sensitive entries never go to public treinos."""
from datetime import datetime
import streamlit as st
from solem_health import MEAL_TYPES, now_local, sleep_minutes
from solem_health_private import delete_entry, list_entries, save_entry
from solem_ui import section_intro

def _time(value, fallback):
    try: return datetime.strptime(str(value), "%H:%M").time()
    except ValueError: return datetime.strptime(fallback, "%H:%M").time()

def _save(client, day, time, kind, details, message, old=None, demo=False):
    entry = {"day": str(day), "logged_at": str(time), "kind": kind, "details": details}
    try: save_entry(client, entry, old=old, demo=demo)
    except Exception:
        st.error("Não foi possível salvar no diário privado. Confira conexão, sessão e migração; seus campos continuam preenchidos.")
        return
    st.session_state["solem_feedback"] = message
    st.rerun()

def _delete(client, entry_id, demo):
    try: delete_entry(client, entry_id, demo=demo)
    except Exception: st.error("Não foi possível remover. Confira a conexão e tente novamente.")
    else:
        st.session_state["solem_feedback"] = "Registro removido do diário privado."
        st.rerun()

def health_page(client, healthy_options, occasional_options, demo=False):
    section_intro("SAÚDE / DIÁRIO", "Seu cuidado, dia após dia.",
                  "Alimentação, água, peso, sono e fotos em um só lugar. Registros privados e manuais.")
    st.caption("Registros antigos em treinos não são migrados automaticamente porque aquela tabela ainda é compartilhada.")
    try: entries = list_entries(client, demo=demo)
    except Exception:
        st.error("Não foi possível carregar o diário privado. Confira a sessão e execute 20260923_health_diary.sql no Supabase.")
        return
    day = st.date_input("Dia em foco", value=now_local().date(), key="health_day")
    selected = [row for row in entries if str(row.get("day", ""))[:10] == str(day)]
    meals = [row for row in selected if row["kind"] == "meal"]
    water_rows = [row for row in selected if row["kind"] == "water"]
    weight = next((row for row in selected if row["kind"] == "weight"), None)
    sleep = next((row for row in selected if row["kind"] == "sleep"), None)
    water = sum(int(row["details"].get("volume_ml", 0)) * int(row["details"].get("quantidade", 0)) for row in water_rows)
    cols = st.columns(4)
    cols[0].metric("Refeições", len(meals))
    cols[1].metric("Água registrada", f"{water:,} ml".replace(",", "."))
    cols[2].metric("Peso", f"{float(weight['details']['kg']):g} kg" if weight else "—")
    cols[3].metric("Sono", f"{sleep['details']['duracao_min']} min" if sleep else "—")
    food_tab, water_tab, weight_tab, sleep_tab, photo_tab = st.tabs(["Alimentação", "Água", "Peso", "Sono", "Fotos"])

    with food_tab:
        st.caption("Adicione quantas refeições precisar no mesmo dia. A classificação é apenas para facilitar o registro.")
        with st.form("health_meal", clear_on_submit=True):
            meal_type = st.selectbox("Tipo de refeição", MEAL_TYPES)
            meal_time = st.time_input("Horário da refeição", value=now_local().time().replace(second=0, microsecond=0))
            a, b = st.columns(2)
            with a:
                healthy = st.multiselect("Alimentos saudáveis / habituais", healthy_options)
                healthy_extra = st.text_input("Outro alimento saudável", max_chars=120)
            with b:
                occasional = st.multiselect("Besteiras / alimentos ocasionais", occasional_options)
                occasional_extra = st.text_input("Outro alimento ocasional", max_chars=120)
            submitted = st.form_submit_button("Salvar refeição", use_container_width=True)
        if submitted:
            good = healthy + ([healthy_extra.strip()] if healthy_extra.strip() else [])
            other = occasional + ([occasional_extra.strip()] if occasional_extra.strip() else [])
            if not good and not other: st.error("Selecione ou descreva ao menos um alimento.")
            else: _save(client, day, meal_time.strftime("%H:%M:%S"), "meal",
                        {"tipo_refeicao": meal_type, "saudaveis": good, "ocasionais": other}, "Refeição registrada.", demo=demo)
        if not meals: st.info("Nenhuma refeição registrada neste dia.")
        for row in sorted(meals, key=lambda item: str(item["logged_at"])):
            details = row["details"]
            with st.container(border=True):
                st.markdown(f"**{details.get('tipo_refeicao', 'Refeição')} · {str(row['logged_at'])[:5]}**")
                st.caption("Saudáveis: " + (", ".join(details.get("saudaveis", [])) or "—"))
                st.caption("Ocasionais: " + (", ".join(details.get("ocasionais", [])) or "—"))
                if st.button("Remover refeição", key=f"meal_delete_{row['id']}"): _delete(client, row["id"], demo)

    with water_tab:
        st.caption("O total diário soma volume × quantidade de cada registro.")
        with st.form("health_water", clear_on_submit=True):
            container = st.selectbox("Recipiente", ["Garrafa", "Copo"])
            volume = st.number_input("Volume por recipiente (ml)", min_value=50, max_value=5000, value=750, step=50)
            amount = st.number_input("Quantidade consumida", min_value=1, max_value=50, value=1)
            drink_time = st.time_input("Horário do registro", value=now_local().time().replace(second=0, microsecond=0))
            st.metric("Total deste registro", f"{volume * amount:,} ml".replace(",", "."))
            submitted = st.form_submit_button("Adicionar água", use_container_width=True)
        if submitted: _save(client, day, drink_time.strftime("%H:%M:%S"), "water",
                            {"recipiente": container, "volume_ml": int(volume), "quantidade": int(amount)}, "Água registrada.", demo=demo)
        for row in sorted(water_rows, key=lambda item: str(item["logged_at"])):
            info = row["details"]
            a, b = st.columns([4, 1])
            a.caption(f"{str(row['logged_at'])[:5]} · {info['quantidade']} × {info['volume_ml']} ml ({info['recipiente']})")
            if b.button("Remover", key=f"water_delete_{row['id']}"): _delete(client, row["id"], demo)
        st.caption(f"Total do dia: {water:,} ml registrados manualmente.".replace(",", "."))

    with weight_tab:
        st.caption("Uma medida por dia; novo salvamento atualiza a anterior.")
        with st.form("health_weight"):
            kg = st.number_input("Peso corporal (kg)", min_value=1.0, max_value=500.0,
                                 value=float(weight["details"]["kg"]) if weight else None, step=0.1,
                                 placeholder="Informe seu peso")
            submitted = st.form_submit_button("Atualizar peso" if weight else "Salvar peso", use_container_width=True)
        if submitted:
            if kg is None: st.error("Informe seu peso antes de salvar.")
            else: _save(client, day, "00:00:00", "weight", {"kg": float(kg)},
                        "Peso atualizado." if weight else "Peso registrado.", old=weight, demo=demo)

    with sleep_tab:
        st.caption("O dia selecionado é o dia em que você acordou. Um registro por dia.")
        previous = sleep["details"] if sleep else {}
        with st.form("health_sleep"):
            bed = st.time_input("Horário em que dormiu", value=_time(previous.get("dormir"), "23:00"), key="sleep_bed")
            wake = st.time_input("Horário em que acordou", value=_time(previous.get("acordar"), "07:00"), key="sleep_wake")
            submitted = st.form_submit_button("Atualizar sono" if sleep else "Salvar sono", use_container_width=True)
        if submitted:
            try: minutes = sleep_minutes(bed.strftime("%H:%M"), wake.strftime("%H:%M"))
            except ValueError as error: st.error(str(error))
            else: _save(client, day, "00:00:00", "sleep",
                        {"dormir": bed.strftime("%H:%M"), "acordar": wake.strftime("%H:%M"), "duracao_min": minutes},
                        "Sono atualizado." if sleep else "Sono registrado.", old=sleep, demo=demo)
        if sleep: st.caption("Duração calculada dos horários informados, sem monitoramento automático.")

    with photo_tab:
        from solem_photos_ui import photo_journal
        photo_journal(day, demo=demo)
