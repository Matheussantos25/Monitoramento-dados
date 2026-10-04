"""Authenticated health diary. New sensitive entries never go to public treinos."""
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
from solem_health import MEAL_TYPES, meal_food_options, now_local, private_weight_history, sleep_minutes
from solem_health_private import delete_entry, list_entries, save_entry
from solem_ui import section_intro

def _time(value, fallback):
    for pattern in ("%H:%M", "%H:%M:%S"):
        try: return datetime.strptime(str(value), pattern).time()
        except ValueError: pass
    return datetime.strptime(fallback, "%H:%M").time()

def _save(client, day, time, kind, details, message, old=None, demo=False):
    entry = {"day": str(day), "logged_at": str(time), "kind": kind, "details": details}
    try: save_entry(client, entry, old=old, demo=demo)
    except Exception:
        st.error("Não foi possível salvar no diário privado. Confira conexão, sessão e migração; seus campos continuam preenchidos.")
        return
    st.session_state["solem_feedback"] = message
    if details.get("input_method") == "photo_reviewed":
        for key in list(st.session_state):
            if key.startswith(f"meal_photo_{day}"): del st.session_state[key]
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
        from solem_meal_photo_ui import photo_meal, daily_metrics, nutrient_metrics, review_meal
        photo_meal(client, day, _save, demo=demo)
        daily_metrics(meals)
        st.caption("Adicione quantas refeições precisar no mesmo dia. A classificação é apenas para facilitar o registro.")
        meal_type = st.selectbox("Tipo de refeição", MEAL_TYPES, key="new_meal_type")
        with st.form("health_meal", clear_on_submit=True):
            meal_time = st.time_input("Horário da refeição", value=now_local().time().replace(second=0, microsecond=0))
            a, b = st.columns(2)
            with a:
                healthy = st.multiselect("Alimentos habituais", meal_food_options(meal_type, healthy_options))
                healthy_extra = st.text_input("Outro alimento habitual", max_chars=120)
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
                st.caption(("Confirmados: " if details.get("nutrition") else "Habituais: ") + (", ".join(details.get("saudaveis", [])) or "—"))
                st.caption("Ocasionais: " + (", ".join(details.get("ocasionais", [])) or "—"))
                if details.get("nutrition"):
                    from solem_meal_analysis import nutrition
                    try: nutrient_metrics(nutrition(details["nutrition"]["items"]))
                    except (KeyError, ValueError, TypeError): st.warning("Confira os dados nutricionais desta refeição antes de editar.")
                    with st.expander("Editar alimentos e porções"):
                        review_meal(client, day, details["nutrition"], _save, f"meal_nutrition_{row['id']}", old=row, demo=demo)
                with st.expander("Editar refeição"):
                    if details.get("nutrition"):
                        st.caption("A edição manual abaixo substitui a análise nutricional. Para preservá-la, use Editar alimentos e porções acima.")
                    previous_type = details.get("tipo_refeicao", "Outra")
                    types = MEAL_TYPES if previous_type in MEAL_TYPES else (*MEAL_TYPES, previous_type)
                    edit_type = st.selectbox("Tipo de refeição", types, index=types.index(previous_type),
                                             key=f"meal_type_{row['id']}")
                    with st.form(f"edit_meal_{row['id']}"):
                        edit_time = st.time_input("Horário da refeição", value=_time(row["logged_at"], "12:00"),
                                                  key=f"meal_time_{row['id']}")
                        a, b = st.columns(2)
                        with a:
                            old_good = details.get("saudaveis", [])
                            edit_good = st.multiselect("Alimentos habituais",
                                meal_food_options(edit_type, healthy_options, old_good), default=old_good,
                                key=f"meal_good_{row['id']}")
                            new_good = st.text_input("Outro alimento habitual", max_chars=120)
                        with b:
                            old_other = details.get("ocasionais", [])
                            edit_other = st.multiselect("Alimentos ocasionais",
                                sorted(set(occasional_options) | set(old_other)), default=old_other,
                                key=f"meal_other_{row['id']}")
                            new_other = st.text_input("Outro alimento ocasional", max_chars=120)
                        edit_submitted = st.form_submit_button("Salvar edição", use_container_width=True)
                    if edit_submitted:
                        good = edit_good + ([new_good.strip()] if new_good.strip() else [])
                        other = edit_other + ([new_other.strip()] if new_other.strip() else [])
                        if not good and not other: st.error("Selecione ou descreva ao menos um alimento.")
                        else: _save(client, day, edit_time.strftime("%H:%M:%S"), "meal",
                                    {"tipo_refeicao": edit_type, "saudaveis": good, "ocasionais": other},
                                    "Refeição atualizada.", old=row, demo=demo)
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
            with st.container(border=True):
                st.caption(f"{str(row['logged_at'])[:5]} · {info['quantidade']} × {info['volume_ml']} ml ({info['recipiente']})")
                with st.expander("Editar água"):
                    with st.form(f"edit_water_{row['id']}"):
                        vessels = ["Garrafa", "Copo"]
                        old_vessel = info.get("recipiente", "Garrafa")
                        if old_vessel not in vessels: vessels.append(old_vessel)
                        edit_vessel = st.selectbox("Recipiente", vessels, index=vessels.index(old_vessel),
                                                   key=f"water_vessel_{row['id']}")
                        edit_volume = st.number_input("Volume por recipiente (ml)", min_value=50, max_value=5000,
                                                      value=int(info.get("volume_ml", 750)), step=50,
                                                      key=f"water_volume_{row['id']}")
                        edit_amount = st.number_input("Quantidade consumida", min_value=1, max_value=50,
                                                      value=int(info.get("quantidade", 1)), key=f"water_amount_{row['id']}")
                        edit_time = st.time_input("Horário do registro", value=_time(row["logged_at"], "12:00"),
                                                  key=f"water_time_{row['id']}")
                        edit_submitted = st.form_submit_button("Salvar edição", use_container_width=True)
                    if edit_submitted: _save(client, day, edit_time.strftime("%H:%M:%S"), "water",
                                             {"recipiente": edit_vessel, "volume_ml": int(edit_volume),
                                              "quantidade": int(edit_amount)}, "Água atualizada.", old=row, demo=demo)
                if st.button("Remover", key=f"water_delete_{row['id']}"): _delete(client, row["id"], demo)
        st.caption(f"Total do dia: {water:,} ml registrados manualmente.".replace(",", "."))

    with weight_tab:
        st.caption("Uma medida por dia. O valor salvo aparece abaixo para você editar e atualizar.")
        with st.form("health_weight"):
            kg = st.number_input("Peso corporal (kg)", min_value=1.0, max_value=500.0,
                                 value=float(weight["details"]["kg"]) if weight else None, step=0.1,
                                 placeholder="Informe seu peso")
            submitted = st.form_submit_button("Salvar edição do peso" if weight else "Salvar peso", use_container_width=True)
        if submitted:
            if kg is None: st.error("Informe seu peso antes de salvar.")
            else: _save(client, day, "00:00:00", "weight", {"kg": float(kg)},
                        "Peso atualizado." if weight else "Peso registrado.", old=weight, demo=demo)
        st.markdown("#### Evolução do peso corporal")
        weight_points = private_weight_history(entries)
        if weight_points:
            fig = go.Figure(go.Scatter(x=[point[0] for point in weight_points],
                                       y=[point[1] for point in weight_points],
                                       mode="lines+markers", line=dict(color="#83DCFF", width=3),
                                       marker=dict(color="#BBA6D9", size=9),
                                       hovertemplate="%{x|%d/%m/%Y}<br>%{y:.1f} kg<extra></extra>"))
            fig.update_layout(xaxis_title=None, yaxis_title="kg", height=300,
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#DCE9F9"), margin=dict(l=5, r=5, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Registre o peso para acompanhar a evolução aqui.")

    with sleep_tab:
        st.caption("O dia selecionado é o dia em que você acordou. Um registro por dia.")
        previous = sleep["details"] if sleep else {}
        with st.form("health_sleep"):
            bed = st.time_input("Horário em que dormiu", value=_time(previous.get("dormir"), "23:00"), key="sleep_bed")
            wake = st.time_input("Horário em que acordou", value=_time(previous.get("acordar"), "07:00"), key="sleep_wake")
            submitted = st.form_submit_button("Salvar edição do sono" if sleep else "Salvar sono", use_container_width=True)
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
