from calendar import monthcalendar
from datetime import date
from html import escape
from pathlib import Path
import base64
import streamlit as st
from solem_calendar import monthly_activity, latest_weight

MONTHS = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']


def character_panel(records, progress):
    latest = latest_weight(records, progress['today'])
    weight = f'{latest[0]:g} kg · registro de {latest[1]:%d/%m/%Y}' if latest else 'Peso ainda não registrado'
    svg = (Path(__file__).parent/'assets/character.svg').read_bytes()
    art = '<img alt="Personagem masculino 2D: explorador Solem" src="data:image/svg+xml;base64,' + base64.b64encode(svg).decode('ascii') + '"/>'
    rank = 'Explorador' if progress['level'] < 5 else 'Construtor' if progress['level'] < 10 else 'Realizador'
    st.html(f'''<section class="character-sheet"><div class="character-art">{art}</div><div class="character-info"><span class="eyebrow">SUA FICHA · {rank.upper()}</span><h2>Seu próximo nível<br>começa no cotidiano.</h2><p>Personagem masculino · 1,70 m<br>{escape(weight)}</p><div class="character-attributes"><span><b>{progress['study_minutes']/60:.1f} h</b> de estudo nesta semana</span><span><b>{progress['week_workouts']} dias</b> de treino nesta semana</span><span><b>Nível {progress['level']:02}</b> · {progress['xp']} XP</span></div><small>Representação ilustrativa, não uma reprodução do seu corpo. Seu peso não altera XP.</small></div></section>''')


def monthly_journal(records, today):
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
    cells = ''.join(f'<div class="month-weekday">{name}</div>' for name in ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'])
    for week in monthcalendar(year, month):
        for n in week:
            if not n:
                cells += '<div class="month-cell outside" aria-hidden="true"></div>'
                continue
            day = date(year, month, n)
            item = days[day]
            state = 'both' if item['study'] and item['workout'] else 'practiced' if item['study'] or item['workout'] else 'rest'
            badges = ('<span>E</span>' if item['study'] else '') + ('<span>T</span>' if item['workout'] else '')
            minutes = f"{item['study_minutes']:.0f} min estudo" if item['study'] else 'Treino' if item['workout'] else 'Futuro' if day > today else 'Descanso'
            label = f'{day:%d/%m/%Y}: {minutes}; treino: {"sim" if item["workout"] else "não"}'
            cells += f'<div class="month-cell {state}{" current" if day == today else ""}" aria-label="{escape(label)}"><b>{n}</b><div class="day-badges">{badges}</div><small>{minutes}</small></div>'
    st.html(f'<div class="month-grid" role="group" aria-label="Calendário de {MONTHS[month-1]} de {year}">{cells}</div>')
    st.caption('E = estudou · T = treinou · os dois marcadores indicam corpo e mente no mesmo dia.')
    selected = st.selectbox('Detalhes do dia', list(days), format_func=lambda d: d.strftime('%d/%m/%Y'), key=f'journal_day_{year}_{month}')
    item = days[selected]
    if not item['activities']:
        st.info('Nenhuma sessão de estudo ou treino registrada neste dia.')
    else:
        st.write(f"Estudo: {item['study_minutes']:.1f} min · Treino cronometrado: {item['workout_minutes']:.1f} min · {item['reps']} repetições · {item['distance']:.2f} km")
        for activity in item['activities']:
            st.text(activity)
    st.caption('Tempo de estudo inclui vídeo-aulas e Anki. Não estimamos duração de exercícios registrados apenas por repetições. Registros futuros e sessões vazias não contam como prática.')
