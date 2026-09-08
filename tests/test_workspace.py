import unittest
from unittest.mock import MagicMock
from solem_workspace import cents, mind_nodes, validate_pdf, validate_item, public_key, Workspace

class WorkspaceTests(unittest.TestCase):
    def test_money_is_exact_and_rejects_ambiguous_input(self):
        self.assertEqual(cents('0,29'),29)
        self.assertEqual(cents('125.50'),12550)
        for value in ('NaN','-1','1.000,00','1e5','1.234','10000000000'):
            with self.assertRaises(ValueError): cents(value)

    def test_mindmap_has_one_root_and_valid_edges(self):
        self.assertEqual(mind_nodes('Raiz\n  Um\n    Filho\n  Dois'), [('Raiz',None,0),('Um',0,1),('Filho',1,2),('Dois',0,1)])
        for body in ('', 'Raiz\nOutra raiz', 'Raiz\n    Salto', 'Raiz\n\tTab', ' Raiz'):
            with self.assertRaises(ValueError): mind_nodes(body)

    def test_pdf_size_and_signature(self):
        validate_pdf(b'%PDF-1.7\n')
        for value in (b'<html>', b'%PDF-'+b'x'*(10*1024*1024)):
            with self.assertRaises(ValueError): validate_pdf(value)

    def test_no_privileged_key(self):
        import base64,json
        jwt=lambda role:'x.'+base64.urlsafe_b64encode(json.dumps({'role':role}).encode()).decode().rstrip('=')+'.x'
        self.assertTrue(public_key(jwt('anon')))
        self.assertFalse(public_key(jwt('service_role')))
        self.assertFalse(public_key('sb_secret_test'))

    def test_optimistic_conflict_does_not_succeed(self):
        client=MagicMock()
        client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value.data=[]
        with self.assertRaisesRegex(ValueError, 'outro dispositivo'):
            Workspace(client).save(dict(kind='note',title='Título',body='Nota'),dict(id='x',revision=2))

    def test_plan_date_time_and_duration(self):
        base=dict(kind='plan',title='Estudar',body='',event_date='2026-09-07',event_time='09:30',duration_minutes=30)
        validate_item(base)
        for patch in (dict(event_time='25:00'),dict(duration_minutes=0),dict(event_date='2026-02-30')):
            with self.assertRaises(ValueError): validate_item(dict(base,**patch))

    def test_ui_modules_render_without_live_secrets(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_string('''
import streamlit as st
from solem_workspace_ui import render_workspace
class Repo: pass
render_workspace(Repo(), [])
''').run()
        self.assertFalse(app.exception)
        for module in ('PDFs','Mapas mentais','Cronograma','Investimentos','Resumos'):
            app.selectbox(key='ws_module').select(module).run()
            self.assertFalse(app.exception, module)

    def test_ui_note_create_edit_and_archive(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_string('''
import streamlit as st
from solem_workspace_ui import render_workspace
if 'fake_items' not in st.session_state: st.session_state.fake_items=[]
class Repo:
    def save(self,item,old=None,new_id=None):
        saved=dict(item,id=old['id'] if old else new_id,revision=old['revision']+1 if old else 1,archived=False)
        st.session_state.fake_items=[x for x in st.session_state.fake_items if x['id']!=saved['id']]+[saved]
        return saved
    def archive(self,item,archived):
        st.session_state.fake_items=[dict(x,archived=archived,revision=x['revision']+1) if x['id']==item['id'] else x for x in st.session_state.fake_items]
render_workspace(Repo(), st.session_state.fake_items)
''').run()
        next(x for x in app.text_input if x.label=='Título').input('Minha nota')
        app.text_area[0].input('Resumo de teste')
        next(x for x in app.button if x.label=='Criar registro').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state['fake_items']),1)
        app.text_area[0].input('Conteúdo editado')
        next(x for x in app.button if x.label=='Salvar alterações').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['fake_items'][0]['body'],'Conteúdo editado')
        self.assertEqual(app.session_state['fake_items'][0]['revision'],2)
        next(x for x in app.button if x.label=='Arquivar').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(app.session_state['fake_items'][0]['archived'])

    def test_mindmap_graph_renders(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_string('''
from solem_workspace_ui import render_workspace
class Repo: pass
render_workspace(Repo(), [dict(id='map-1',kind='mindmap',title='Mapa',body='Raiz\\n  Filho',archived=False,revision=1)])
''').run()
        app.selectbox(key='ws_module').select('Mapas mentais').run()
        app.radio(key='ws_select_mindmap_False').set_value('map-1').run()
        self.assertFalse(app.exception)

    def test_dedicated_note_collection_and_markdown_reading(self):
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_string('''
from solem_workspace_ui import render_workspace
class Repo: pass
render_workspace(Repo(), [dict(id='note-1',kind='note',title='Minha página',body='# Meu resumo\\n\\n**Conceito importante**',archived=False,revision=1)], 'Anotações')
''').run()
        self.assertFalse(app.exception)
        self.assertFalse(app.selectbox)
        app.radio(key='ws_select_note_False').set_value('note-1').run()
        app.radio(key='ws_view_note_note-1').set_value('Leitura').run()
        self.assertFalse(app.exception)
        self.assertTrue(any('# Meu resumo' in x.value for x in app.markdown))
        self.assertFalse(app.text_area)
