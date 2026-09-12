"""Rank UI keeps progress derived from the shared history, without database writes."""
import io
import math
import struct
import wave
from pathlib import Path
import base64
import streamlit as st
from solem_ranks import ranks, NAMES, REP_LIMITS, ACCURACY_LIMITS, SAMPLE_LIMITS

def emblem(tier, width):
    data = (Path(__file__).parent / 'assets/ranks' / f'rank_{tier}.svg').read_bytes()
    st.html(f'<img alt="Insígnia {NAMES[tier]}" width="{width}" src="data:image/svg+xml;base64,{base64.b64encode(data).decode()}"/>')

def promotion_sound():
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        for frequency in [523.25, 659.25, 783.99]:
            for i in range(2400):
                envelope = min(1, i / 160) * (1 - i / 2400)
                wav.writeframesraw(struct.pack('<h', int(4000 * envelope * math.sin(2 * math.pi * frequency * i / 16000))))
    return buffer.getvalue()

def promotion_overlay(tier, label):
    data = (Path(__file__).parent / 'assets/ranks' / f'rank_{tier}.svg').read_bytes()
    source = base64.b64encode(data).decode()
    st.html(f'''<section class="rank-promotion" role="status" aria-live="polite">
        <div class="rank-promotion__veil"></div>
        <div class="rank-promotion__rays" aria-hidden="true"></div>
        <div class="rank-promotion__ring" aria-hidden="true"></div>
        <div class="rank-promotion__content">
            <span>PROMOÇÃO DE ELO</span>
            <img src="data:image/svg+xml;base64,{source}" alt="Insígnia {NAMES[tier]}" />
            <h2>{NAMES[tier]}</h2>
            <p>{label}</p>
        </div>
    </section>''')

def rank_panel(records, topics, today):
    data = ranks(records, topics, today)
    st.subheader('Sua jornada ranqueada')
    st.caption('Físico por repetições acumuladas · Estudos por acerto e volume de questões em cada tópico do edital.')
    with st.expander('Efeitos e regras dos elos'):
        st.caption('As promoções são celebradas automaticamente com animação e som. Sem perda por descanso. Corrigir ou excluir registros recalcula os elos; a celebração não se repete ao atualizar a página. O navegador pode bloquear áudio automático até a primeira interação.')
        st.dataframe([{'Elo': n, 'Repetições acumuladas': REP_LIMITS[i], 'Acerto mínimo (%)': ACCURACY_LIMITS[i], 'Questões mínimas por tópico': SAMPLE_LIMITS[i]} for i, n in enumerate(NAMES)], hide_index=True)
        st.caption('Faixas propostas para gamificação pessoal, não um sistema competitivo Elo. Estudos usam todo o histórico válido; não são uma previsão de aprovação. Físico conta repetições totais, sem multiplicar séries. Cardio e isometria continuam no calendário e XP, sem conversão artificial em repetições.')
    current = {'physical': data['physical_tier'], **{(x['discipline'], x['topic']): x['tier'] for x in data['topics']}}
    previous = st.session_state.get('rank_high_water')
    promotions = [(key, tier) for key, tier in current.items() if previous is not None and tier > previous.get(key, tier)]
    promoted = bool(promotions)
    st.session_state['rank_high_water'] = {k: max(v, (previous or {}).get(k, v)) for k, v in current.items()}
    if promoted:
        promoted_key, promoted_tier = max(promotions, key=lambda item: item[1])
        promoted_label = 'Elo físico' if promoted_key == 'physical' else f'{promoted_key[0]} · {promoted_key[1]}'
        promotion_overlay(promoted_tier, promoted_label)
        with st.container(key='rank_promotion_audio'):
            st.audio(promotion_sound(), format='audio/wav', autoplay=True)
    art, detail = st.columns([1,4], vertical_alignment='center')
    with art:
        emblem(data['physical_tier'], 180)
    with detail:
        st.metric('Elo físico', data['physical_rank'], delta=f"{data['reps']:,} repetições registradas", delta_color='off')
    tier = data['physical_tier']
    if tier < 7:
        start, target = REP_LIMITS[tier:tier + 2]
        st.progress((data['reps'] - start) / (target - start), text=f"Próximo elo: {NAMES[tier + 1]} · faltam {target - data['reps']} repetições, no seu ritmo")
    else:
        st.caption('Mestre alcançado. Mantenha sua rotina e respeite o descanso.')
    discipline = st.selectbox('Elos por disciplina do edital', list(topics), key='rank_discipline')
    selected = [x for x in data['topics'] if x['discipline'] == discipline]
    topic_name = st.selectbox('Insígnia do tópico', [x['topic'] for x in selected], key='rank_topic_emblem')
    selected_rank = next((x for x in selected if x['topic'] == topic_name), None)
    if selected_rank and selected_rank['tier'] >= 0:
        emblem(selected_rank['tier'], 150)
        st.caption(selected_rank['rank'])
    placed = sum(x['tier'] >= 0 for x in data['topics'])
    st.caption(f"Cobertura do edital: {placed}/{len(data['topics'])} tópicos com pelo menos 20 questões classificáveis.")
    st.dataframe([{'Tópico': x['topic'], 'Elo': x['rank'], 'Acerto (%)': round(x['accuracy'], 1) if x['total'] else None, 'Questões': x['total'], 'Próximo passo': f"Resolver mais {20 - x['total']} questões" if x['total'] < 20 else ('Manter a revisão' if x['tier'] == 7 else f"{NAMES[x['tier']+1]}: ≥{SAMPLE_LIMITS[x['tier']+1]} questões e ≥{ACCURACY_LIMITS[x['tier']+1]}% de acerto")} for x in selected], hide_index=True, use_container_width=True)
    if data['ignored']:
        st.info(f"{data['ignored']} questões não entram nos elos por tópico: tema genérico, múltiplos tópicos ou nome diferente do edital. Os registros originais foram preservados. Anki não entra nesta classificação.")
