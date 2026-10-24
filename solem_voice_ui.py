"""Voice is an optional draft input; saving stays in the existing authenticated forms."""
from hashlib import sha256
import streamlit as st
from solem_audio import transcribe_audio
from solem_voice import parse_meal, parse_weight, parse_sleep, parse_workout

EXAMPLES = {
    'meal': 'Almoço, arroz 170, feijão 323, ovo cozido 371, peso acumulado.',
    'weight': 'Peso 67 vírgula 5 quilos.',
    'sleep': 'Dormi às 3 e acordei às 13:30, na mesma data.',
    'workout': 'Agachamento, 3 séries de 20, descanso de 60 segundos.',
}


def voice_input(kind, key, *, foods=None, exercises=None, current=None, fields=None):
    with st.expander('🎙 Preencher por voz · conferir antes de salvar'):
        st.caption('Grave até 60 segundos e toque em parar. O áudio é enviado ao servidor do Solem para transcrição pelo Whisper, sem API paga. Não é salvo no histórico. Confira o texto antes de preencher.')
        st.caption('Preenche apenas este formulário, na data selecionada. Exemplo: ' + EXAMPLES[kind])
        audio = st.audio_input('Gravar fala · toque no microfone para começar e no quadrado para parar',
                               sample_rate=16000, key=key+'_audio',
                               help='Permita o microfone no navegador. A primeira transcrição pode demorar enquanto o modelo é carregado.')
        if audio is not None:
            data = audio.getvalue()
            digest = sha256(data).hexdigest()
            retry = False
            if st.session_state.get(key+'_audio_error') and st.session_state.get(key+'_audio_seen') == digest:
                st.warning(st.session_state[key+'_audio_error'])
                retry = st.button('Tentar transcrever novamente', key=key+'_retry')
            if digest != st.session_state.get(key+'_audio_seen') or retry:
                st.session_state[key+'_audio_seen'] = digest
                st.session_state.pop(key+'_audio_error', None)
                try:
                    with st.spinner('Transcrevendo no Solem… Na primeira vez, aguarde o carregamento do modelo.'):
                        st.session_state[key+'_text'] = transcribe_audio(data)
                except ValueError as error:
                    st.session_state[key+'_audio_error'] = str(error)
                except Exception:
                    # Never surface audio, credentials or provider diagnostics in the UI/log.
                    st.session_state[key+'_audio_error'] = 'O transcritor não carregou. Tente novamente em instantes ou digite o texto abaixo.'
                if st.session_state.get(key+'_audio_error'):
                    st.rerun()
                st.success('Fala transcrita. Confira o texto e os valores abaixo; nada foi salvo.')
        st.caption('Se o microfone não abrir, permita o acesso nas configurações do site no Opera e recarregue. Você também pode corrigir ou digitar a fala abaixo.')
        text = st.text_area('O que você falou · pode corrigir', key=key+'_text', max_chars=2000)
        if not text.strip(): return None
        try:
            if kind == 'meal': result = parse_meal(text, foods)
            elif kind == 'weight': result = parse_weight(text)
            elif kind == 'sleep': result = parse_sleep(text)
            else:
                result = parse_workout(text, exercises, current)
                allowed = fields(result['exercise'])
                if any(field not in allowed for field in result['values']):
                    raise ValueError('Há medidas que não pertencem a este exercício. Confira exercício, duração e repetições.')
            if kind == 'meal':
                labels = {f['id']: f.get('display_name', f['name']) for f in foods}
                st.write(('Peso acumulado da balança' if result['cumulative'] else 'Peso individual de cada alimento') + ' · ' + (result['meal_type'] or 'tipo de refeição atual'))
                st.caption('Prato tarado: leitura inicial 0 g. A lista falada substitui o rascunho deste formulário. Confira também as referências de preparo abaixo.')
                st.table([{'Alimento': labels.get(item['food_id'],item['name']), 'Leitura (g)': f'{reading:g}', 'Porção (g)': f"{item['grams']:g}"} for item, reading in zip(result['items'], result['readings'])])
            elif kind == 'weight': st.write(f"Peso: {result['kg']:g} kg")
            elif kind == 'sleep': st.write(f"Dormiu {result['bed']} · acordou {result['wake']} · " + {'auto':'datas automáticas','same':'mesma data','previous':'noite anterior'}[result['mode']])
            else:
                st.write(result['exercise'])
                labels = {'series':'Séries','repeticoes':'Repetições totais','carga_kg':'Carga (kg)','descanso_seg':'Descanso (s)','duracao_min':'Duração (min)','distancia_km':'Distância (km)','isometria_segundos':'Tempo sustentado (s)'}
                st.table([{'Campo': labels[k], 'Valor': v} for k,v in result['values'].items()])
            st.caption('Ainda não está salvo. Confira, preencha e use o botão de salvar do formulário.')
            if st.button('Preencher campos', key=key+'_apply'): return result
        except ValueError as error: st.warning(str(error))
    return None


def meal_voice_draft(proposal, key):
    """New meals only. A revision gets fresh widget keys so a prior draft cannot leak."""
    from solem_meal_analysis import catalog
    result = voice_input('meal', key+'_voice', foods=catalog())
    if result:
        revision = int(st.session_state.get(key+'_voice_revision', 0)) + 1
        st.session_state[key+'_voice_revision'] = revision
        st.session_state[key+'_voice_proposal'] = result
    result = st.session_state.get(key+'_voice_proposal')
    if result:
        draft_key = key+'_dictated_'+str(st.session_state[key+'_voice_revision'])
        proposal = {'items': result['items'], 'voice_cumulative':result['cumulative'], 'voice_type':result['meal_type'],
                    'voice_weighing': {'baseline_g':0, 'readings_g':result['readings']} if result['cumulative'] else {}}
        return proposal, draft_key
    return proposal, key
