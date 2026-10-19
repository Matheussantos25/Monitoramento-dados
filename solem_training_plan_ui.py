"""Separate workout dashboard; keeps the existing general journal intact."""
from calendar import monthrange
from datetime import date, timedelta
import streamlit as st
from solem_training_plan import plan_day, workout_day
from solem_journal_component import journal_calendar


def training_plan_panel(records, today, preferences=None, generic=False, calendar=True):
    from solem_ui import navigate_checkup
    st.subheader("Seu treino, em duas frentes")
    stats = workout_day(records, today, preferences, generic, today)
    plan = plan_day(records, today, enabled=not generic)
    a, b = st.columns(2)
    with a:
        st.markdown("**Treino base · metas atuais**")
        value = stats["base_pct"]
        st.metric("Cumprimento base", "—" if value is None else f"{value}%")
        if value is not None: st.progress(value / 100)
    with b:
        st.markdown("**Plano complementar · core e costas**")
        value = stats["plan_pct"]
        st.metric("Cumprimento do plano", "Recuperação" if plan["recovery"] else "—" if value is None else f"{value}%")
        if value is not None: st.progress(value / 100)
    st.caption("Cada exercício tem o mesmo peso no percentual, limitado a 100%. Fazer mais de um não compensa deixar outro sem fazer. As metas base não foram alteradas.")
    if not generic:
        st.markdown(f"#### Hoje · {plan['title']}")
        st.caption(f"{plan['duration']} extras, não duas horas obrigatórias. Sem carga adicional sugerida.")
        if plan["recovery"]:
            st.info("Hoje o plano não pede esforço extra. Recuperação não é falha, nem vira 100% automaticamente. Ajuste também suas metas base se estiver cansado.")
        for goal in plan["goals"]:
            with st.container(border=True):
                st.markdown(f"**{goal['exercise']}** · {goal['value']:g} / {goal['target']:g} {goal['unit']}")
                st.progress(goal["fraction"])
                st.caption(f"Sugestão: {goal['sets']} séries de {goal['target'] / goal['sets']:g} {goal['unit']} · descanso {goal['rest_seconds']} s. Registre o total realizado, não a meta planejada.")
                st.caption(f"Referência: {goal['history_days']} dias com essa medida nas 4 semanas anteriores." if goal["history_days"] >= 2 else "Pouco histórico recente dessa medida: ponto de partida conservador, não teste de capacidade máxima.")
                st.button("Registrar " + goal["exercise"], key=f"plan_register_{goal['id']}",
                          on_click=navigate_checkup, args=("Treino", goal["exercise"]), use_container_width=True)
        with st.expander("Ver semana e como o plano funciona"):
            for index, label in enumerate(("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")):
                item = plan_day(records, plan["week"] + timedelta(days=index))
                description = " · ".join(f"{g['exercise']}: {g['target']:g} {g['unit']}" for g in item["goals"]) or "Sem volume extra"
                st.markdown(f"**{label} · {item['title']}** — {description}")
            st.caption("Metas calculadas com 70% da mediana diária registrada nas 4 semanas anteriores à segunda-feira, dentro de limites conservadores. Essa é uma regra de organização do app, não uma fórmula clínica validada nem uma prescrição da ACSM. Não sobem durante a semana. Você pode fazer menos ou descansar conforme a recuperação.")
            st.warning("Seu histórico não mede técnica, recuperação, gordura corporal ou carga máxima segura. Pare antes da falha técnica (deixe cerca de 2–3 repetições possíveis); interrompa com dor, tontura ou falta de ar incomum. Sem barra disponível, não improvise suporte: pule o exercício e ajuste com um profissional. Descanso é permitido, inclusive nas metas base.")
            st.caption("Fortalecer o abdômen não remove gordura localizada nem garante definição em um prazo. Alimentação, sono e recuperação também importam. Referência: ACSM 2026 · https://acsm.org/resistance-training-guidelines-update-2026/")
    if calendar:
        with st.expander("Abrir calendário · somente treinos", expanded=False):
            workout_calendar(records, today, preferences, generic)


def workout_calendar(records, today, preferences=None, generic=False):
    st.markdown("#### Calendário de treino")
    st.caption("Somente exercícios. B = metas base atuais; P = plano daquela semana. Alterar registros antigos recalcula os percentuais. Dias anteriores ao início do plano não recebem uma meta retroativa.")
    year_col, month_col = st.columns(2)
    with year_col: year = st.number_input("Ano do treino", 1900, 2200, today.year, key="workout_calendar_year")
    with month_col: month = st.selectbox("Mês do treino", range(1, 13), index=today.month - 1, key="workout_calendar_month")
    days = [workout_day(records, date(year, month, n), preferences, generic, today)
            for n in range(1, monthrange(year, month)[1] + 1)]
    journal_calendar(year, month, today, days, key_prefix="workout_calendar")
