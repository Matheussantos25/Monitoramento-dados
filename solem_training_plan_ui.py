"""Separate workout dashboard; keeps the existing general journal intact."""
from calendar import monthrange
from html import escape
from datetime import date, timedelta
import streamlit as st
from solem_training_plan import plan_day, workout_day
import solem_journal_component
from solem_training_cycle import START, CYCLE, REVISED, cycle_config, clean_rows, goals_at


def training_plan_panel(records, today, preferences=None, generic=False, calendar=True):
    from solem_ui import navigate_checkup
    st.subheader("Seu ciclo de treino" if not generic else "Seu treino")
    day = st.date_input("Dia do ciclo", today, key="cycle_selected_day") if not generic else today
    future = day > today
    stats = workout_day(records, day, preferences, generic, today)
    plan = plan_day(records, day, enabled=not generic)
    preview_cycle = cycle_config(max(day, date.fromisoformat(REVISED["starts_on"])))
    preview_start = date.fromisoformat(preview_cycle["starts_on"])
    a, b = st.columns(2)
    with a:
        st.markdown("**Base do ciclo · incluída na sessão**" if plan.get("cycle") else "**Treino base · metas atuais**")
        value = stats["base_pct"]
        st.metric("Cumprimento base", "—" if value is None else f"{value}%")
        if value is not None: st.progress(value / 100)
    with b:
        st.markdown("**Sessão completa · corpo inteiro**" if plan.get("cycle") else "**Plano complementar · core e costas**")
        value = stats["plan_pct"]
        st.metric("Cumprimento do plano", "Recuperação" if plan["recovery"] else "—" if value is None else f"{value}%")
        if value is not None: st.progress(value / 100)
    st.caption("Estes indicadores são do plano de treino; o check-up segue suas metas personalizadas. Os mesmos registros contam nos dois painéis: não some os volumes nem registre o mesmo treino duas vezes. No ciclo, a base já está incluída na sessão completa.")
    if not generic:
        st.info(f"Ciclo revisado: {preview_start:%d/%m} a {preview_start + timedelta(days=27):%d/%m/%Y}. Três sessões de força com seis exercícios, duas caminhadas e recuperação no fim de semana. Dias anteriores a 26/10 mantêm o plano original.")
        if plan.get("cycle_week"):
            st.markdown(f"**Semana {plan['cycle_week']}/4 · {plan['phase']}**")
        if plan.get("held"):
            st.info("Etapa mantida: faltaram registros suficientes de conclusão na semana anterior. Não compense sessões perdidas acumulando volume.")
        if plan.get("completed"):
            st.info("Ciclo encerrado. Revise seus resultados e recuperação antes de iniciar outro. Suas metas personalizadas continuam no check-up.")
        st.markdown(f"#### {'Hoje' if day == today else day.strftime('%d/%m')} · {plan['title']}")
        st.caption(f"{plan['duration']} · sessão total, incluindo a base." if plan.get("cycle") else f"{plan['duration']} · regra anterior ao ciclo.")
        if plan["recovery"]:
            st.info("Recuperação: sem treino obrigatório do ciclo hoje. Não é falha nem vira 100% automaticamente." if plan.get("cycle") else "Recuperação do plano anterior. O novo ciclo começa em 22/10.")
        if plan["recovery"]:
            next_day = next((day + timedelta(days=i) for i in range(1, 8) if plan_day(records, day + timedelta(days=i))["goals"]), None)
            if next_day:
                def show_next(): st.session_state["cycle_selected_day"] = next_day
                st.button(f"Ver próxima sessão · {next_day:%d/%m}", key="cycle_next_session", on_click=show_next)
        if plan["goals"]:
            done = sum(g["fraction"] >= 1 for g in plan["goals"])
            st.caption("Prévia: o registro fica disponível no dia da sessão." if future else "Consulta do histórico: registre novas sessões no dia de hoje." if day < today else f"{done} de {len(plan['goals'])} exercícios concluídos · cada card acompanha um exercício.")
        for start in range(0, len(plan["goals"]), 2):
            columns = st.columns(2, gap="small")
            for column, goal in zip(columns, plan["goals"][start:start+2]):
                with column, st.container(key=f"cycle_card_{goal['id']}"):
                    status = "Programado" if future else "Concluído" if goal["fraction"] >= 1 else "Em andamento"
                    amount = "—" if future else f"{goal['value']:g}"
                    pct = 0 if future else goal["fraction"] * 100
                    st.html(f'''<div class="checkup-card"><span class="checkup-card__top">{escape(goal['exercise'])}<small>{status}</small></span>
                        <strong>{amount} <span>/ {goal['target']:g} {escape(goal['unit'])}</span></strong>
                        <progress value="{pct:.1f}" max="100" aria-label="Progresso de {escape(goal['exercise'])}">{pct:.0f}%</progress></div>''')
                    st.markdown("**5 km no total do dia**" if goal["unit"] == "km" else f"**{goal['sets']} séries × {goal['target']/goal['sets']:g} {goal['unit']}** · descanso {goal['rest_seconds']} s")
                    st.button("Ver registro" if goal["fraction"] >= 1 and not future else "Registrar →", key=f"plan_register_{goal['id']}",
                              on_click=navigate_checkup, args=("Treino", goal["exercise"]), use_container_width=True, disabled=day != today)
                    with st.expander("Orientação da sessão"):
                        st.caption(goal.get("note", "Registre o total realizado e as séries reais."))
                        if goal.get("fallback"): st.caption("Barra sem referência suficiente por série: remada como alternativa.")
                        if goal.get("history"): st.caption(f"Base: {goal['history_days']} registros anteriores com séries válidas. A meta não é um teste máximo.")
        with st.expander(f"Semana de {plan['week']:%d/%m} · metas dessas datas"):
            st.caption("Esta seção mostra a semana da data selecionada, inclusive a versão antiga quando você consulta dias anteriores a 26/10.")
            for index, label in enumerate(("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")):
                item = plan_day(records, plan["week"] + timedelta(days=index))
                description = " · ".join(f"{g['exercise']}: {g['target']:g} {g['unit']}" for g in item["goals"]) or "Sem volume extra"
                st.markdown(f"**{label} · {plan['week'] + timedelta(days=index):%d/%m} · {item['title']}** — {description}")
            st.caption("No novo ciclo, flexão e agachamento partem da capacidade que você relatou. Nos demais, usamos registros com 2–8 séries anteriores ao ciclo: 80% da mediana por série, com limites conservadores. Sem referência suficiente na barra, usamos remada. Essa é uma heurística do app, não uma avaliação clínica. As metas não sobem com os registros da própria semana.")
            st.warning("Seu histórico não mede técnica, recuperação, gordura corporal ou carga máxima segura. Pare antes da falha técnica (deixe cerca de 2–3 repetições possíveis); interrompa com dor, tontura ou falta de ar incomum. Sem barra disponível, não improvise suporte: pule o exercício e ajuste com um profissional. Descanso é permitido, inclusive nas metas base.")
            st.caption("Fortalecer o abdômen não remove gordura localizada nem garante definição em um prazo. Alimentação, sono e recuperação também importam. Referência: ACSM 2026 · https://acsm.org/resistance-training-guidelines-update-2026/")
        with st.expander("Ver as 4 semanas · progressão planejada", expanded=today < preview_start):
            st.caption("Prévia se houver progressão. Para avançar, são necessárias pelo menos 2 sessões de força com 80% de cada exercício na semana anterior. Isso mede registros, não técnica ou recuperação: reduza ou descanse se necessário. A semana 4 sempre reduz o volume. Faça 5–10 minutos de aquecimento leve e séries fáceis antes da força.")
            preview = st.selectbox("Semana do ciclo", range(4), format_func=lambda i: f"{i+1} · {preview_cycle['labels'][i]}", key="cycle_preview_week")
            first = preview_start + timedelta(days=preview * 7)
            st.caption(f"{first:%d/%m} a {first + timedelta(days=6):%d/%m} · descanso de 90–150 s entre séries; deixe 2–3 repetições possíveis.")
            rows = clean_rows(records)
            for offset in range(7):
                when = first + timedelta(days=offset)
                goals = goals_at(rows, when, preview, preview_cycle)
                title = preview_cycle["days"][when.weekday()]["title"]
                details = " · ".join(f"{g['exercise']}: {g['sets']}×{g['per_set']:g} {g['unit']}" for g in goals) or "Sem meta obrigatória"
                st.markdown(f"**{when:%d/%m} · {title}** — {details}")
    if calendar:
        with st.expander("Abrir calendário · somente treinos", expanded=False):
            workout_calendar(records, today, preferences, generic)


def workout_calendar(records, today, preferences=None, generic=False):
    st.markdown("#### Calendário de treino")
    st.caption("Somente exercícios. Durante o ciclo, B = base do ciclo; P = sessão completa, que já inclui B. São metas do plano, não do check-up personalizado. Datas anteriores mantêm a regra antiga. Alterar registros recalcula os percentuais.")
    year_col, month_col = st.columns(2)
    with year_col: year = st.number_input("Ano do treino", 1900, 2200, today.year, key="workout_calendar_year")
    with month_col: month = st.selectbox("Mês do treino", range(1, 13), index=today.month - 1, key="workout_calendar_month")
    days = [workout_day(records, date(year, month, n), preferences, generic, today)
            for n in range(1, monthrange(year, month)[1] + 1)]
    # The low-level component's keyword interface already existed before this
    # panel. Cloud may retain the old four-argument journal_calendar wrapper
    # after a deploy; do not require its newer key_prefix argument here.
    solem_journal_component._calendar(
        year=year, month=month, today=today.isoformat(), days=days,
        key=f"workout_calendar_{year}_{month}", default=None)
