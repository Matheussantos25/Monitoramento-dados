import json
from uuid import uuid4
import streamlit as st
import streamlit.components.v1 as components
from solem_vocabulary import vocabulary_data, vocabulary_body, dictionary, image_search, card_html, anki_package
from solem_workspace import Workspace
from solem_workspace_ui import require_login, safe_error

lookup = st.cache_data(ttl=86400, max_entries=200, show_spinner=False)(dictionary)
images = st.cache_data(ttl=86400, max_entries=100, show_spinner=False)(image_search)


def copy_card(front, back):
    payload = json.dumps([front, back], ensure_ascii=True).replace("<", "\\u003c")
    components.html('''<style>body{font:15px system-ui;color:#eaf4ff;margin:0}button{background:#183348;color:#eaf4ff;border:1px solid #83dcff;border-radius:8px;padding:12px;margin:4px;cursor:pointer}#status{font-size:13px}</style>
<button onclick="copy(0)">Copiar frente</button><button onclick="copy(1)">Copiar verso</button><p id="status" role="status"></p>
<script>const cards=''' + payload + ''';
async function copy(i){const holder=document.createElement('div');holder.innerHTML=cards[i];
try {await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([cards[i]],{type:'text/html'}),'text/plain':new Blob([holder.textContent],{type:'text/plain'})})]);document.getElementById('status').textContent='Copiado. Cole no campo correspondente do Anki.';}
catch(e){document.body.appendChild(holder);const r=document.createRange();r.selectNodeContents(holder);const s=getSelection();s.removeAllRanges();s.addRange(r);const ok=document.execCommand('copy');s.removeAllRanges();holder.remove();document.getElementById('status').textContent=ok?'Copiado. Confira a formatação ao colar.':'Cópia bloqueada. Use o HTML abaixo ou baixe o pacote.';}}
</script>''', height=105)


def vocabulary_panel(demo=False):
    st.subheader("Seu baralho de vocabulário")
    st.caption("Frase na frente, significado e imagem no verso. Revise aqui ou exporte para o Anki.")
    try:
        repo = None if demo else Workspace(require_login())
        items = st.session_state.setdefault("demo_vocabulary_items", []) if demo else repo.list()
    except Exception as error:
        st.error(safe_error(error)); return
    if st.session_state.pop("vocab_saved", False):
        st.success("Palavra salva no seu caderno.")
    review_tab, editor_tab = st.tabs(["Revisar", "Criar e editar"])
    with review_tab:
        from solem_vocabulary_review_ui import review_panel
        review_panel(items, repo)
    with editor_tab:
        trash = st.toggle("Lixeira do vocabulário", key="vocab_trash")
        search = st.text_input("Buscar no caderno", key="vocab_search")
        choices = {x["id"]: x for x in items if vocabulary_data(x) and x.get("archived", False) == trash
                   and search.casefold() in (x["title"]+x["body"]).casefold()}
        pending = st.session_state.pop("vocab_next", None)
        if pending in choices:
            st.session_state["vocab_selected"] = pending
        if st.session_state.get("vocab_selected") not in choices:
            st.session_state["vocab_selected"] = "new"
        selected = st.selectbox("Palavra do caderno", ["new"]+list(choices), format_func=lambda k: "＋ Nova palavra" if k == "new" else choices[k]["title"], key="vocab_selected")
        old = choices.get(selected)
        if trash:
            if old and st.button("Restaurar palavra"):
                try:
                    if repo: repo.archive(old, False)
                    else: old["archived"] = False
                    st.rerun()
                except Exception as error: st.error(safe_error(error))
            return
        data = vocabulary_data(old) or {}
        key = f"vocab_{selected}_{old.get('revision', 0) if old else st.session_state.get('vocab_generation', 0)}"
        for field in ("word", "sentence", "definition", "context", "source", "forms", "image", "image_page", "image_credit"):
            st.session_state.setdefault(key+field, data.get(field, ""))
        word = st.text_input("Palavra ou expressão em inglês", key=key+"word", max_chars=100, placeholder="Ex.: stumble", on_change=lambda: st.session_state.update({key+"forms": ""}))
        st.caption("Buscar envia apenas a palavra ao FreeDictionaryAPI.com. A busca de imagem envia apenas o termo ao Wikimedia Commons. Sem API paga.")
        if st.button("Buscar significado e exemplo", disabled=not word.strip()):
            try:
                with st.spinner("Consultando o dicionário…"):
                    st.session_state[key+"senses"] = lookup(word)
                    st.session_state[key+"lookup_word"] = word
                    if not st.session_state.get(key+"image_query"):
                        st.session_state[key+"image_query"] = word
                if not st.session_state[key+"senses"]: st.info("Palavra não encontrada. Você pode salvar agora e preencher manualmente depois.")
            except Exception:
                st.warning("Dicionário indisponível ou palavra não encontrada. Seus campos continuam aqui; tente novamente ou preencha manualmente.")
        senses = st.session_state.get(key+"senses", []) if st.session_state.get(key+"lookup_word") == word else []
        if senses:
            index = st.selectbox("Escolha o sentido usado na cena", range(len(senses)), format_func=lambda i: senses[i]["part"]+" · "+senses[i]["definition"], key=key+"sense")
            sense = senses[index]
            if sense["sentence"]: st.write("Exemplo do dicionário: "+sense["sentence"])
            else: st.caption("Este sentido não tem exemplo. Use a frase que ouviu na série.")
            if st.button("Usar este significado", key=key+"use"):
                st.session_state[key+"definition"] = sense["definition"]
                st.session_state[key+"source"] = sense["source"]
                st.session_state[key+"forms"] = sense.get("forms", "")
            if sense["sentence"] and st.button("Usar exemplo do dicionário", key=key+"example"):
                st.session_state[key+"sentence"] = sense["sentence"]
                st.session_state[key+"source"] = sense["source"]
                st.session_state[key+"forms"] = sense.get("forms", "")
        st.markdown("**Front · Frente**")
        st.caption("A palavra informada acima aparece em negrito no cartão.")
        sentence = st.text_area("Frase em inglês (da série ou do dicionário)", key=key+"sentence", max_chars=2000)
        st.markdown("**Back · Verso**")
        definition = st.text_area("Significado em inglês", key=key+"definition", max_chars=3000)
        context = st.text_input("Série, episódio ou contexto (opcional)", key=key+"context", max_chars=300)
        with st.expander("Imagem para lembrar da palavra"):
            term = st.text_input("O que a imagem deve mostrar?", value=word, key=key+"image_query", max_chars=100)
            if st.button("Buscar imagens gratuitas", disabled=not term.strip()):
                try:
                    with st.spinner("Buscando imagens…"): st.session_state[key+"images"] = images(term)
                    if not st.session_state[key+"images"]: st.info("Sem imagens. Tente um termo mais concreto.")
                except Exception: st.warning("Busca indisponível. Você pode continuar sem imagem e adicionar depois.")
            for i, picture in enumerate(st.session_state.get(key+"images", [])):
                with st.container(border=True):
                    st.image(picture["image"], width=220)
                    st.caption(picture["title"]+" · "+picture["image_credit"])
                    if st.button("Usar esta imagem", key=key+"img"+str(i)):
                        for field in ("image", "image_page", "image_credit"): st.session_state[key+field] = picture[field]
            if st.session_state[key+"image"]:
                st.caption("Imagem selecionada · "+st.session_state[key+"image_credit"])
                if st.button("Remover imagem", key=key+"remove_image"):
                    for field in ("image", "image_page", "image_credit"): st.session_state[key+field] = ""
        current = dict(word=word, sentence=sentence, definition=definition, context=context,
                       **{f: st.session_state[key+f] for f in ("source", "forms", "image", "image_page", "image_credit")})
        if "review" in data: current["review"] = data["review"]
        if current["source"]: st.caption(current["source"])
        if st.button("Salvar palavra" if not old else "Salvar alterações da palavra", type="primary", disabled=not word.strip()):
            try:
                item = dict(kind="note", title=word.strip(), body=vocabulary_body(current))
                if repo: saved = repo.save(item, old, new_id=st.session_state.setdefault(key+"id", str(uuid4())))
                elif old:
                    old.update(item); old["revision"] += 1; saved = old
                else:
                    saved = dict(item, id=str(uuid4()), revision=1, archived=False); items.append(saved)
                st.session_state["vocab_next"] = saved["id"]
                st.session_state["vocab_saved"] = True
                st.session_state["vocab_generation"] = st.session_state.get("vocab_generation", 0)+1
                st.rerun()
            except Exception as error: st.error(safe_error(error))
        if old and st.button("Mover palavra para a lixeira"):
            try:
                if repo: repo.archive(old, True)
                else: old["archived"] = True
                st.rerun()
            except Exception as error: st.error(safe_error(error))
        st.subheader("Prévia do card")
        try:
            front, back = card_html(current)
        except ValueError as error:
            st.info(str(error)); return
        with st.container(border=True):
            st.caption("FRENTE"); st.html(front)
        with st.container(border=True):
            st.caption("VERSO"); st.html(back)
        copy_card(front, back)
        st.caption("Copie e cole nos campos do Anki. Imagens coladas por link precisam de internet; para manter a imagem offline, use o pacote abaixo. Confira a formatação ao colar.")
        with st.expander("HTML e pacote para importar no Anki"):
            st.code(front, language="html"); st.code(back, language="html")
            st.write("O ZIP contém card.txt e a imagem. No Anki para computador, coloque a imagem em collection.media e importe card.txt com HTML habilitado; depois sincronize com o celular. Não é um .apkg.")
            fingerprint = json.dumps(current, sort_keys=True)
            if st.button("Preparar pacote com imagem"):
                try:
                    st.session_state[key+"package"] = (fingerprint, anki_package(current))
                except Exception: st.warning("Não foi possível preparar a imagem. Tente outra ou remova a imagem e exporte novamente.")
            package = st.session_state.get(key+"package")
            if package and package[0] == fingerprint:
                st.download_button("Baixar pacote para Anki", package[1], "solem-anki.zip", "application/zip")
        st.caption("Preparar ou exportar um card não aumenta seu contador de cards adicionados ao Anki.")
