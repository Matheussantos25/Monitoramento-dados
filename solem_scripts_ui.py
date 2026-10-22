from pathlib import Path
from uuid import uuid4
import streamlit as st
import streamlit.components.v1 as components
from solem_scripts import script_data, script_body
from solem_workspace import Workspace, validate_item
from solem_workspace_ui import require_login, safe_error

_prompter=components.declare_component("solem_teleprompter",path=str(Path(__file__).parent/"assets/teleprompter"))

def scripts_page(demo=False):
    st.header("Ideias e roteiros")
    st.caption("Capture uma ideia, desenvolva seu roteiro e ensaie no teleprompter. Privado na sua conta.")
    repo=None
    try:
        if demo:
            items=st.session_state.setdefault("demo_script_items",[])
        else:
            client=require_login()
            client.auth.get_user()
            repo=Workspace(client)
            items=repo.list()
    except Exception as error:
        st.error(safe_error(error)); return
    feedback=st.session_state.pop("script_feedback",None)
    if feedback: st.success(feedback)
    search=st.text_input("Buscar título, texto ou tags",key="script_search")
    trash=st.toggle("Lixeira de ideias e roteiros",key="script_trash")
    choices={x["id"]:x for x in items if script_data(x) and x.get("archived",False)==trash
             and search.casefold() in (x["title"]+x["body"]).casefold()}
    next_selected=st.session_state.pop("script_next",None)
    if next_selected in choices: st.session_state["script_selected"]=next_selected
    if st.session_state.get("script_selected") not in choices:
        st.session_state["script_selected"]="new"
    selected=st.selectbox("Abrir documento",["new"]+list(choices),
        format_func=lambda k:"＋ Nova ideia ou roteiro" if k=="new" else choices[k]["title"],key="script_selected")
    old=choices.get(selected)
    data=script_data(old) if old else dict(type="idea",text="",description="",tags="")
    if trash:
        if old and st.button("Restaurar documento"):
            try:
                if repo: repo.archive(old,False)
                else: old["archived"]=False
                st.rerun()
            except Exception as error: st.error(safe_error(error))
        return
    key=f"script_{selected}_{old.get('revision',1) if old else 0}"
    with st.form(key):
        kind=st.selectbox("Tipo",["Ideia","Roteiro"],index=int(data["type"]=="script"))
        title=st.text_input("Título",value=old["title"] if old else "",max_chars=160)
        description=st.text_area("Possível descrição da publicação",value=data["description"],max_chars=3000,height=100)
        tags=st.text_input("Tags (separadas por vírgula)",value=data["tags"],max_chars=500)
        text=st.text_area("Ideia / texto do roteiro",value=data["text"],max_chars=40000,height=360)
        submitted=st.form_submit_button("Salvar documento")
    if submitted:
        try:
            item=dict(kind="note",title=title.strip(),body=script_body("script" if kind=="Roteiro" else "idea",text,description,tags))
            validate_item(item)
            if repo: saved=repo.save(item,old)
            elif old:
                old.update(item);old["revision"]+=1;saved=old
            else:
                saved=dict(item,id=str(uuid4()),revision=1,archived=False);items.append(saved)
            st.session_state["script_next"]=saved["id"]
            st.session_state["script_feedback"]="Documento salvo. Seu teleprompter está pronto abaixo."
            st.rerun()
        except Exception as error: st.error(safe_error(error))
    if old:
        if st.button("Mover documento para a lixeira"):
            try:
                if repo: repo.archive(old,True)
                else: old["archived"]=True
                st.rerun()
            except Exception as error: st.error(safe_error(error))
        if data["text"].strip():
            st.subheader("Teleprompter")
            st.caption("Lê a versão salva. Play não grava áudio ou vídeo. Ao trocar de aba, a leitura pausa.")
            _prompter(text=data["text"],title=old["title"],key=f"prompter_{old['id']}_{old.get('revision',1)}",default=None)
