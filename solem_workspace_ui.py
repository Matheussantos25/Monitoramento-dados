"""Authenticated personal modules. Never authenticate the cached legacy client."""
import json
from uuid import uuid4
from datetime import date, time
import streamlit as st
from supabase import create_client
from solem_workspace import Workspace, KINDS, cents, mind_nodes, public_key

def safe_error(error):
    if isinstance(error, ValueError):
        return str(error)
    code = str(getattr(error, 'code', ''))
    if code in ('42P01', 'PGRST205'):
        return 'A biblioteca pessoal ainda precisa ser ativada no mesmo projeto Supabase.'
    return 'Não foi possível concluir. Verifique a conexão e sua sessão. Seus campos não foram apagados. Se o envio de PDF já ocorreu, tente baixá-lo antes de reenviar.'


def _private_client():
    try:
        url = st.secrets.get('SUPABASE_URL', '')
        key = st.secrets.get('SUPABASE_PUBLISHABLE_KEY', '') or st.secrets.get('SUPABASE_KEY', '')
    except Exception:
        url, key = '', ''
    if not url.startswith('https://') or not public_key(key):
        return None
    if 'private_client' not in st.session_state:
        st.session_state.private_client = create_client(url, key)
    return st.session_state.private_client


def logout_private():
    client = st.session_state.get('private_client')
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass
    for key in list(st.session_state):
        if key.startswith(('private_', 'ws_')):
            del st.session_state[key]
    st.session_state.solem_page = 'Visão geral'


def require_login():
    client = _private_client()
    if client is None:
        st.error('O acesso não está configurado. Adicione a URL e a chave pública do Supabase nos Secrets do Streamlit.')
        st.stop()
    if client.auth.get_session():
        return client
    st.html('''<style>[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"]{display:none!important}header[data-testid="stHeader"]{height:0!important}</style><section class="auth-intro"><div class="auth-mark">✳</div><h1>Seu espaço começa aqui.</h1><p>Entre para acessar seu histórico, sua evolução e sua biblioteca pessoal em um único lugar.</p></section>''')
    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        with st.form('private_login', clear_on_submit=True):
            email = st.text_input('E-mail', max_chars=254)
            password = st.text_input('Senha', type='password', max_chars=256)
            mode = st.radio('Conta', ['Entrar', 'Criar conta'], horizontal=True)
            submit = st.form_submit_button('Continuar', use_container_width=True)
        if submit:
            if not email.strip() or not password:
                st.error('Preencha e-mail e senha.')
            else:
                try:
                    with st.spinner('Conectando…'):
                        if mode == 'Entrar':
                            client.auth.sign_in_with_password({'email':email.strip(), 'password':password})
                        else:
                            client.auth.sign_up({'email':email.strip(), 'password':password})
                    if client.auth.get_session():
                        st.rerun()
                    st.info('Confira seu e-mail para confirmar a conta e depois entre.')
                except Exception:
                    st.error('Não foi possível entrar. Confira e-mail, senha e confirmação da conta.')
    st.stop()


def workspace_page(module):
    client = require_login()
    st.header(module)
    st.caption('Um lugar para suas ideias, referências e próximos passos.')
    repo = Workspace(client)
    try:
        client.auth.get_user()  # Validate identity with Auth before showing private records.
        with st.spinner('Carregando seus registros privados…'):
            items = repo.list()
    except Exception as error:
        st.error(safe_error(error))
        st.button('Entrar novamente', on_click=logout_private)
        return
    render_workspace(repo, items, module)

def render_workspace(repo, items, module=None):
    message = st.session_state.pop('ws_feedback', None)
    if message:
        st.success(message)
    if module is None:
        module = st.selectbox('Módulo', list(KINDS), key='ws_module')
    kind = KINDS[module]
    library, document = st.columns([1, 3], gap='large')
    with library:
        st.markdown('##### Páginas')
        st.button('Atualizar', key='ws_refresh', use_container_width=True)
        search = st.text_input('Buscar por título ou conteúdo', key='ws_search', placeholder='Buscar nesta coleção…', label_visibility='collapsed')
        archived = st.toggle('Mostrar arquivados', key='ws_archived')
        filtered = [x for x in items if x['kind'] == kind and x['archived'] == archived and search.casefold() in (x['title']+' '+x['body']).casefold()]
        if kind == 'plan':
            month = st.date_input('Mês do cronograma', value=date.today(), key='ws_month')
            filtered = sorted([x for x in filtered if (x.get('event_date') or '').startswith(month.strftime('%Y-%m'))], key=lambda x:(x['event_date'],x['event_time']))
        by_id = {x['id']:x for x in filtered}
        selection_key = f'ws_select_{kind}_{archived}'
        next_selected = st.session_state.pop('ws_next_selected', None)
        if next_selected in by_id:
            st.session_state[selection_key] = next_selected
        if st.button('＋ Nova página', disabled=archived, use_container_width=True):
            st.session_state[selection_key] = 'new'
        st.caption(f'{len(filtered)} páginas' if filtered else 'Sua coleção começa com uma página.')
        selected = st.radio('Abrir ou editar', ['new']+list(by_id), format_func=lambda x:'Página em branco' if x == 'new' else by_id[x]['title'], key=selection_key, label_visibility='collapsed')
    with document:
        with st.container(key='document_canvas'):
            if kind == 'plan' and filtered:
                st.dataframe([{'Data':x['event_date'],'Horário':x['event_time'],'Atividade':x['title'],'Minutos':x['duration_minutes'],'Concluído':x['done']} for x in filtered], hide_index=True, use_container_width=True)
            if kind == 'investment':
                cost = sum(x['invested_cents'] for x in filtered)
                value = sum(x['value_cents'] for x in filtered)
                a,b,c = st.columns(3)
                a.metric('Aplicado', f'R$ {cost/100:,.2f}')
                b.metric('Saldo informado', f'R$ {value/100:,.2f}')
                c.metric('Diferença nominal', f'R$ {(value-cost)/100:,.2f}')
                st.caption('Valores manuais em reais, nas datas informadas.')
            render_document(repo, kind, archived, selected, by_id.get(selected))

def render_document(repo, kind, archived, selected, old):
    st.caption('COLEÇÃO / ' + next(k for k,v in KINDS.items() if v == kind).upper())
    st.subheader(old['title'] if old else 'Sem título')
    if old:
        if kind == 'mindmap':
            try:
                nodes = mind_nodes(old['body'])
                lines = ['digraph { rankdir=LR; node [shape=box, style=rounded];']
                for i,(label,parent,_) in enumerate(nodes):
                    lines.append(f'n{i} [label={json.dumps(label)}];')
                    if parent is not None:
                        lines.append(f'n{parent} -> n{i};')
                st.graphviz_chart('\n'.join(lines+['}']))
            except ValueError as error:
                st.warning(str(error))

        if st.button('Restaurar' if archived else 'Arquivar', key=f'ws_archive_{old["id"]}'):
            try:
                repo.archive(old, not archived)
                st.session_state.ws_feedback = 'Registro restaurado.' if archived else 'Registro arquivado. Você pode restaurá-lo pelo filtro de arquivados.'
                st.rerun()
            except Exception as error:
                st.error(safe_error(error))
        if kind == 'pdf' and not archived:
            with st.expander('Enviar PDF ou recuperar envio interrompido'):
                upload = st.file_uploader('PDF de até 10 MB', type=['pdf'], max_upload_size=10, key=f'ws_pdf_{old["id"]}')
                if st.button('Enviar arquivo', disabled=upload is None):
                    try:
                        repo.upload(old, upload.getvalue())
                        st.success('PDF enviado. Disponível para baixar nesta conta.')
                    except Exception as error:
                        st.error(safe_error(error))
            if st.button('Preparar download do PDF'):
                try:
                    data = repo.download(old)
                    st.download_button('Baixar PDF privado', data, file_name=f'{old["id"]}.pdf', mime='application/pdf')
                except Exception as error:
                    st.error(safe_error(error))
    if archived:
        st.caption('Restaure um item para editá-lo ou acessar o PDF.')
        return
    if old:
        snapshot_key = f'ws_snapshot_{old["id"]}'
        if snapshot_key not in st.session_state:
            st.session_state[snapshot_key] = old
        if st.button('Recarregar editor (descarta campos não salvos)'):
            st.session_state[snapshot_key] = old
            st.rerun()
        old = st.session_state[snapshot_key]
    base = old or {}
    if kind in ('note','summary'):
        st.caption('A leitura mostra a versão salva. Salve suas alterações antes de trocar de modo ou página.')
        mode = st.radio('Modo da página', ['Editar', 'Leitura'], horizontal=True, key=f'ws_view_{kind}_{selected}')
        if mode == 'Leitura':
            st.markdown(base.get('body') or '*Esta página ainda está em branco.*')
            return
    if kind in ('note','summary'):
        st.caption('Markdown: # título · **negrito** · - lista · [texto](link). Salve para sincronizar.')
    draft_key = f'ws_draft_{kind}'
    if draft_key not in st.session_state:
        st.session_state[draft_key] = str(uuid4())
    with st.form(f'ws_form_{kind}_{selected}_{base.get("revision",0)}'):
        title = st.text_input('Título', value=base.get('title',''), max_chars=160)
        if kind == 'mindmap':
            st.caption('Escreva uma raiz. Use 2 espaços para cada nível filho; até 80 tópicos e 5 níveis. A árvore visual aparece após salvar.')
        body = st.text_area('Conteúdo / observações', value=base.get('body',''), height=480 if kind in ('note','summary') else 260, max_chars=50000)
        event_date, event_time, duration, done, invested, current = None, '', 0, False, 0, 0
        if kind in ('plan','investment'):
            event_date = st.date_input('Data' if kind == 'plan' else 'Data do saldo', value=date.fromisoformat(base['event_date']) if base.get('event_date') else date.today(), min_value=date(1900,1,1), max_value=date(2200,12,31))
        if kind == 'plan':
            event_time = st.time_input('Horário local', value=time.fromisoformat(base.get('event_time') or '09:00')).strftime('%H:%M')
            duration = st.number_input('Duração em minutos', min_value=1, max_value=1440, value=base.get('duration_minutes',30))
            done = st.checkbox('Concluído', value=base.get('done',False))
        if kind == 'investment':
            invested = st.text_input('Total aplicado (R$, sem separador de milhar)', value=f"{base.get('invested_cents',0)/100:.2f}")
            current = st.text_input('Saldo atual informado (R$)', value=f"{base.get('value_cents',0)/100:.2f}")
        submit = st.form_submit_button('Salvar alterações' if old else 'Criar registro')
    if submit:
        try:
            item = dict(kind=kind,title=title.strip(),body=body,event_date=str(event_date) if event_date else None,event_time=event_time,duration_minutes=int(duration),done=done,invested_cents=cents(invested) if kind == 'investment' else 0,value_cents=cents(current) if kind == 'investment' else 0)
            saved = repo.save(item, old, st.session_state[draft_key])
            st.session_state['ws_next_selected'] = saved['id']
            st.session_state.pop(f'ws_snapshot_{saved["id"]}', None)
            st.session_state[draft_key] = str(uuid4())
            st.session_state.ws_feedback = 'Página salva. Agora você pode anexar seu PDF.' if kind == 'pdf' else 'Página salva.'
            st.rerun()
        except Exception as error:
            st.error(safe_error(error))
