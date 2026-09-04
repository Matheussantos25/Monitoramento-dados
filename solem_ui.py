"""Solem presentation components. Native widgets keep keyboard and form behavior."""
from html import escape
from pathlib import Path
import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go
from solem_progress import calculate_progress

PAGES = ["Visão geral", "Treino", "Evolução física", "Alimentação", "Peso", "Estudar", "Evolução nos estudos", "Prompts", "Configurações"]


def apply_theme():
    st.html("<style>" + (Path(__file__).parent / "assets" / "solem.css").read_text(encoding="utf-8") + "</style>")
    pio.templates["solem"] = go.layout.Template(layout=dict(
        colorway=["#C6E58B", "#89B8C5", "#BBA6D9", "#E5BE8B"],
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Segoe UI, sans-serif", color="#EDF1E8", size=13),
        xaxis=dict(gridcolor="#2A322B", zerolinecolor="#2A322B"),
        yaxis=dict(gridcolor="#2A322B", zerolinecolor="#2A322B"),
        margin=dict(l=20, r=20, t=35, b=25)))
    pio.templates.default = "solem"


def navigate(page):
    st.session_state["solem_page"] = page


def shell(df):
    progress = calculate_progress(df.to_dict("records"))
    st.html(f'''<header class="solem-header"><div class="solem-brand"><span class="solem-logo" aria-hidden="true">✳</span><div>solem<span class="brand-sub">CORPO & MENTE</span></div></div><div class="header-status"><span class="status-dot"></span> Seu espaço de evolução <span class="header-level">Nível {progress['level']:02}</span></div></header>''')
    page = st.radio("Navegação principal", PAGES, horizontal=True, key="solem_page", label_visibility="collapsed")
    message = st.session_state.pop("solem_feedback", None)
    if message:
        st.toast(message, icon=":material/check_circle:")
    return page, progress


def section_intro(eyebrow, title, description):
    st.html(f'<div class="section-intro"><span class="eyebrow">{escape(eyebrow)}</span><h1>{escape(title)}</h1><p>{escape(description)}</p></div>')


def goal_panel(title, current, target, unit):
    pct = min(100, max(0, current / target * 100)) if target > 0 else 0
    st.html(f'''<section class="goal-panel"><div><span class="eyebrow">{escape(title)}</span><h3>{current:,} <small>/ {target:,} {escape(unit)}</small></h3></div><span class="goal-label">{'Meta alcançada' if current >= target else 'Em progresso'}</span><progress value="{pct}" max="100" aria-label="{escape(title)}">{pct:.0f}%</progress></section>'''.replace(",", "."))


def overview(p):
    today = p["today"]
    months = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    weekdays = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    st.html(f'<div class="overview-heading"><div><span class="eyebrow">SEU PAINEL PESSOAL</span><h1>Pequenos passos.<br><span>Uma nova versão de você.</span></h1></div><span class="date-label">{weekdays[today.weekday()]}<br>{today.day} de {months[today.month-1]}, {today.year}</span></div>')

    hero, journey = st.columns([1.65, 1], gap="medium")
    with hero:
        st.html(f'''<section class="journey-hero"><div class="hero-copy"><span class="eyebrow">SUA JORNADA, NO SEU RITMO</span><h2>Consistência é<br>o seu superpoder.</h2><p>Treine o corpo. Alimente a mente.<br>Cada atividade registrada conta.</p><span class="hero-stat">{p['week_days']} dias ativos <span>nesta semana</span></span></div><div class="solar-art" aria-hidden="true"><div class="orbit orbit-outer"></div><div class="orbit orbit-inner"></div><div class="sun-core">✳</div><span class="orbit-point"></span><span class="orbit-caption">EM CONSTANTE<br>EVOLUÇÃO</span></div></section>''')
    with journey:
        st.html(f'''<section class="level-panel"><div class="panel-top"><span class="eyebrow">SEU PROGRESSO</span><span class="mini-tag">{p['xp']:,} XP no total</span></div><div class="level-row"><div class="level-emblem">{p['level']:02}</div><div><span class="muted">Nível atual</span><h2>{'Explorador' if p['level'] < 5 else 'Construtor' if p['level'] < 10 else 'Realizador'}</h2></div></div><div class="xp-label"><span>{p['level_xp']} / 250 XP</span><span>Nível {p['level'] + 1:02} ↗</span></div><progress value="{p['level_xp']}" max="250" aria-label="Experiência para o próximo nível"></progress><p class="level-caption">Faltam {250-p['level_xp']} XP para o próximo nível.</p><div class="streak-row"><span class="streak-icon" aria-hidden="true">↗</span><div><strong>{p['streak']} {'dia' if p['streak'] == 1 else 'dias'} de sequência</strong><span>Seu histórico continua valendo a cada retomada.</span></div></div></section>''')

    st.html(f'''<section class="weekly-stats" aria-label="Resumo da semana"><div><span>DIAS DE TREINO</span><strong>{p['week_workouts']:02}<small> nesta semana</small></strong></div><div><span>TEMPO DE ESTUDO</span><strong>{int(p['study_minutes']//60)}<small>h </small>{int(p['study_minutes']%60):02}<small>min</small></strong></div><div><span>QUESTÕES RESOLVIDAS</span><strong>{p['questions']}<small> nesta semana</small></strong></div><div><span>EXPERIÊNCIA DE HOJE</span><strong>+{p['today_xp']}<small> XP conquistados</small></strong></div></section>''')

    missions, rhythm = st.columns([1.65, 1], gap="medium")
    with missions:
        st.html('<div class="section-title"><h2>Seu próximo passo</h2><span>Um pouco a cada dia</span></div>')
        for category, title, description, xp, destination, glyph in [
            ("treino", "Coloque o corpo em movimento", "Registre uma atividade do seu treino.", 30, "Treino", "↗"),
            ("estudo", "Abra espaço para o foco", "Salve uma sessão de estudo ou revisão.", 30, "Estudar", "▤"),
            ("alimentação", "Cuide da sua rotina", "Preencha seu diário alimentar.", 10, "Alimentação", "◉"),
        ]:
            done = category in p["today_categories"]
            with st.container(key=f"mission_{category}"):
                a, b = st.columns([4, 1], vertical_alignment="center")
                with a:
                    st.html(f'<div class="mission"><span class="mission-icon {"done" if done else ""}" aria-hidden="true">{"✓" if done else glyph}</span><div><h3>{title}</h3><p>{description}</p></div><span class="mission-xp">{"Concluído" if done else f"+{xp} XP"}</span></div>')
                with b:
                    st.button("Ver registro" if done else "Começar →", key=f"go_{category}", on_click=navigate, args=(destination,), use_container_width=True)
        st.caption("Corpo e mente no mesmo dia: +15 XP. Descansar também faz parte do caminho.")
    with rhythm:
        st.html('<div class="section-title"><h2>Seu ritmo</h2><span>Esta semana</span></div>')
        cells = ""
        for i, day in enumerate(p["week"]):
            state = "active" if day in p["days"] else "future" if day > today else "rest"
            current = " today" if day == today else ""
            desc = "atividade registrada" if day in p["days"] else "dia futuro" if day > today else "sem atividade"
            cells += f'<div class="week-day {state}{current}"><span>{["S", "T", "Q", "Q", "S", "S", "D"][i]}</span><div aria-label="{day.strftime("%d/%m")}: {desc}">{"✓" if day in p["days"] else day.day}</div></div>'
        st.html(f'<section class="rhythm-panel"><div class="week-grid">{cells}</div><div class="week-legend"><span><i></i> Atividade registrada</span><span>◌ Hoje</span></div><div class="rhythm-note"><strong>Todo recomeço conta.</strong><p>Seus pontos e conquistas permanecem no histórico, mesmo depois de uma pausa.</p></div></section>')

    st.html('<div class="section-title achievements-title"><h2>Marcos da jornada</h2><span>Conquistas do seu histórico</span></div>')
    badges = ""
    for mark, title, description, value, target in p["achievements"]:
        unlocked = value >= target
        badges += f'<article class="achievement {"unlocked" if unlocked else "locked"}"><div class="badge-art">{mark}</div><h3>{title}</h3><p>{description}</p><span>{"✓ Conquistado" if unlocked else f"{value} de {target} dias"}</span></article>'
    st.html(f'<section class="achievement-grid">{badges}</section>')
    with st.expander("Como funcionam os pontos e as conquistas?"):
        st.write("Você recebe 30 XP por dia com treino, 30 XP por dia com estudo e 10 XP por dia com alimentação registrada. Treino e estudo no mesmo dia rendem mais 15 XP. Cada categoria pontua uma única vez ao dia, independentemente da quantidade de registros. Cada nível exige 250 XP.")
        st.write("Registros vazios ou futuros não pontuam. Peso, carga e quantidade de comida não geram pontos. A sequência considera dias consecutivos com atividade e permanece ativa se o último foi ontem. Os marcos contam dias acumulados, sem exigir sequência. Editar ou excluir atividades recalcula o progresso a partir do histórico disponível.")
    st.html('<div class="section-title"><h2>Atividades recentes</h2><span>O caminho que você já percorreu</span></div>')
    if not p["recent"]:
        st.info("Sua jornada começa com um registro. Escolha um dos passos acima para ver sua evolução aqui.")
    else:
        rows = ""
        for day, category, row in p["recent"]:
            rows += f'<div class="activity-row"><span class="activity-kind">{escape(category.capitalize())}</span><strong>{escape(str(row.get("exercicio", "Atividade")))}</strong><span>{day.strftime("%d/%m/%Y")}</span></div>'
        st.html(f'<section class="activity-list">{rows}</section>')
    st.html('<div class="solem-footer"><span>solem / corpo & mente</span><span>O progresso é pessoal. O ritmo também.</span></div>')
