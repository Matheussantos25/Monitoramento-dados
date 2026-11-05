import time
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
from solem_vocabulary import vocabulary_data, vocabulary_body, card_html
from solem_vocabulary_review import review_state, schedule_review, RATINGS, interval_label
from solem_workspace_ui import safe_error


def review_panel(items, repo=None):
    now = int(time.time())
    ready, incomplete = [], 0
    for item in items:
        data = vocabulary_data(item)
        if not data or item.get('archived'): continue
        try: card_html(data)
        except ValueError:
            incomplete += 1; continue
        ready.append((item, data, review_state(data.get('review'))))
    due = sorted((x for x in ready if x[2]['due_at'] <= now),
                 key=lambda x: (x[2]['reviews']==0, x[2]['due_at'], str(x[0]['id'])))
    a,b,c=st.columns(3)
    a.metric('Para revisar agora',len(due)); b.metric('Novos',sum(x[2]['reviews']==0 for x in ready)); c.metric('No baralho',len(ready))
    st.caption('Leia a frente, tente lembrar e revele a resposta. A próxima revisão depende da sua avaliação.')
    if incomplete: st.caption(f'{incomplete} cartão(ões) aguardando frase, palavra em destaque ou significado em Criar e editar.')
    if st.button('Atualizar fila',key='vocab_review_refresh'): st.rerun()
    if not due:
        st.success('Tudo revisado por enquanto.' if ready else 'Crie seu primeiro cartão em Criar e editar.')
        if ready:
            upcoming=min(x[2]['due_at'] for x in ready)
            st.caption('Próxima revisão: '+datetime.fromtimestamp(upcoming,ZoneInfo('America/Sao_Paulo')).strftime('%d/%m às %H:%M'))
        return
    item,data,state=due[0]
    token=f"{item['id']}_{item.get('revision',0)}"
    revealed=st.session_state.get('vocab_revealed')==token
    front,back=card_html(data)
    with st.container(border=True):
        st.caption('FRENTE · lembre do significado da palavra em negrito')
        st.html('<div style="font-size:1.55rem;line-height:1.65;padding:12px 4px">'+front+'</div>')
        if revealed:
            st.divider(); st.caption('VERSO · significado e imagem'); st.html(back.replace('max-height:320px','max-height:220px'))
        elif st.button('Mostrar resposta',key='vocab_reveal_'+token,type='primary',width='stretch'):
            st.session_state['vocab_revealed']=token; st.rerun()
    if revealed:
        st.caption('Errei: não lembrei · Difícil: lembrei com esforço · Bom: lembrei · Fácil: imediato')
        for col,rating in zip(st.columns(4),RATINGS):
            updated=schedule_review(state,rating,now)
            label=rating+' · '+interval_label(updated['due_at']-now)
            if col.button(label,key='vocab_rate_'+token+'_'+rating,width='stretch'):
                try:
                    payload=dict(kind='note',title=item['title'],body=vocabulary_body(dict(data,review=updated)))
                    if repo: repo.save(payload,item)
                    else: item.update(payload); item['revision']=item.get('revision',0)+1
                except Exception as error:
                    st.error(safe_error(error))
                else:
                    st.session_state.pop('vocab_revealed',None); st.rerun()
