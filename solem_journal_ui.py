from datetime import date
from html import escape
from pathlib import Path
import base64
import streamlit as st
from solem_calendar import monthly_activity, latest_weight, daily_events
from solem_journal_component import journal_calendar

MONTHS = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']


def character_panel(records, progress):
    latest = latest_weight(records, progress['today'])
    weight = f'{latest[0]:g} kg · registro de {latest[1]:%d/%m/%Y}' if latest else 'Peso ainda não registrado'
    svg = (Path(__file__).parent/'assets/character.svg').read_bytes()
    art = '<img alt="Personagem masculino 2D: explorador Solem" src="data:image/svg+xml;base64,' + base64.b64encode(svg).decode('ascii') + '"/>'
    rank = 'Explorador' if progress['level'] < 5 else 'Construtor' if progress['level'] < 10 else 'Realizador'
    st.html(f'''<section class="character-sheet"><div class="character-art">{art}</div><div class="character-info"><span class="eyebrow">SUA FICHA · {rank.upper()}</span><h2>Seu próximo nível<br>começa no cotidiano.</h2><p>Personagem masculino · 1,70 m<br>{escape(weight)}</p><div class="character-attributes"><span><b>{progress['study_minutes']/60:.1f} h</b> de estudo nesta semana</span><span><b>{progress['week_workouts']} dias</b> de treino nesta semana</span><span><b>Nível {progress['level']:02}</b> · {progress['xp']} XP</span></div><small>Representação ilustrativa, não uma reprodução do seu corpo. Seu peso não altera XP.</small></div></section>''')


def monthly_journal(records, today, private_entries=None):
    if private_entries is None:
        private_entries = st.session_state.get("overview_health_entries")
    st.subheader('Diário de consistência')
    st.caption('Um mês de cada vez. Estudos e treinos reais, sem penalizar seus dias de descanso.')
    a,b = st.columns([1,2])
    with a:
        year = st.number_input('Ano', min_value=1900, max_value=2200, value=today.year, step=1, key='journal_year')
    with b:
        month = st.selectbox('Mês', list(range(1,13)), index=today.month-1, format_func=lambda n: MONTHS[n-1], key='journal_month')
    days = monthly_activity(records, year, month, today)
    study_days = sum(d['study'] for d in days.values())
    workout_days = sum(d['workout'] for d in days.values())
    hours = sum(d['study_minutes'] for d in days.values())/60
    st.html(f'<div class="journal-summary"><span><b>{study_days}</b> dias de estudo</span><span><b>{workout_days}</b> dias de treino</span><span><b>{hours:.1f} h</b> estudadas</span></div>')
    calendar_days = []
    for day, item in days.items():
        events = daily_events(records, private_entries, day) if day <= today else []
        calendar_days.append({"date": day.isoformat(), "study": item["study"],
                              "workout": item["workout"], "study_minutes": item["study_minutes"],
                              "health": any(event["kind"] in ("Saúde", "Alimentação", "Peso") for event in events),
                              "events": events})
    journal_calendar(year, month, today, calendar_days)
    st.caption('Toque em um dia para ver os registros. E = estudou · T = treinou · + = saúde.')
    st.caption('Tempo de estudo inclui vídeo-aulas e Anki. Não estimamos duração de exercícios registrados apenas por repetições. Registros futuros e sessões vazias não contam como prática.')
