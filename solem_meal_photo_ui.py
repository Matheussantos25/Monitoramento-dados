"""Streamlit photo-assisted meals. Photos live only in the current upload session."""
from hashlib import sha256
from uuid import uuid4
import streamlit as st
from solem_health import MEAL_TYPES, now_local
from solem_photos_ui import normalized_jpeg
from solem_meal_analysis import catalog, nutrition, recognize, meal_details, day_nutrition


def nutrient_metrics(result):
    title = "Estimativa parcial" if not result.get("complete", True) else "Estimativa nutricional"
    st.caption(title + " · porções aproximadas, não medidas. Óleo, molhos e preparo podem alterar os valores.")
    values = result["totals"]
    cols = st.columns(3)
    for index, (key, label, unit) in enumerate([
        ("kcal", "Energia", "kcal"), ("protein_g", "Proteínas", "g"), ("carbs_g", "Carboidratos", "g"),
        ("fat_g", "Gorduras", "g"), ("fiber_g", "Fibras", "g")]):
        cols[index % 3].metric(label, f"≈ {values[key]:.1f} {unit}")
    if result.get("missing"):
        st.warning(f"{result['missing']} alimento(s) sem porção ou correspondência nutricional. Não estão incluídos no total; isso não significa zero calorias.")


def daily_metrics(meals):
    result = day_nutrition(meals)
    if result["counted"]:
        with st.expander("Nutrição registrada no dia", expanded=True):
            nutrient_metrics({"totals": result["totals"], "complete": not result["partial"]})
            st.caption(f"{result['counted']} de {len(meals)} refeição(ões) com cálculo. Valores parciais quando há registros manuais ou alimentos não calculados.")


def review_meal(client, day, proposal, save, key, old=None, demo=False):
    table = catalog()
    labels = {food["id"]: food["name"] for food in table}
    source_items = proposal["items"]
    items = []
    st.markdown("#### Confira seu prato")
    st.caption("Confirme alimento, preparo e porção. Se não souber, mantenha a sugestão como aproximada ou use 0 g para não calcular.")
    for index, item in enumerate(source_items):
        with st.container(border=True):
            name = st.text_input("Alimento", value=item["name"], max_chars=80, key=f"{key}_name_{index}")
            chosen = st.selectbox("Referência nutricional / preparo", [""] + list(labels),
                index=([""] + list(labels)).index(item.get("food_id", "") if item.get("food_id", "") in labels else ""),
                format_func=lambda food_id: labels.get(food_id, "Sem correspondência — não calcular"), key=f"{key}_food_{index}")
            grams = st.number_input("Porção estimada (g)", min_value=0.0, max_value=2000.0,
                value=float(item["grams"]), step=10.0, key=f"{key}_grams_{index}")
            include = st.checkbox("Incluir este alimento", value=True, key=f"{key}_include_{index}")
            st.caption("Identificação sugerida: " + {"high": "mais provável", "medium": "incerta", "low": "confira com atenção"}.get(item.get("confidence"), "confira com atenção"))
            if chosen:
                food = next(food for food in table if food["id"] == chosen)
                st.link_button("Consultar fonte USDA", food["source_url"])
            if include: items.append({"name": name, "food_id": chosen, "grams": grams, "confidence": item.get("confidence", "low")})
    # Add missing ingredients without another AI request (also supports manual corrections).
    added = st.multiselect("Adicionar alimento que faltou", list(labels), format_func=labels.get, key=f"{key}_added")
    for food_id in added:
        grams = st.number_input(f"Porção de {labels[food_id]} (g)", 0.0, 2000.0, 0.0, 10.0, key=f"{key}_extra_{food_id}")
        items.append({"name": labels[food_id], "food_id": food_id, "grams": grams, "confidence": "low"})
    valid = False
    try:
        result = nutrition(items)
        nutrient_metrics(result)
        valid = True
    except ValueError as error: st.info(str(error))
    previous = old.get("details", {}) if old else {}
    previous_type = previous.get("tipo_refeicao", "Almoço")
    types = list(dict.fromkeys([*MEAL_TYPES, previous_type]))
    meal_type = st.selectbox("Refeição", types, index=types.index(previous_type), key=f"{key}_type")
    from datetime import time
    previous_time = time.fromisoformat(str(old["logged_at"])) if old else now_local().time().replace(second=0, microsecond=0)
    meal_time = st.time_input("Horário", value=previous_time, key=f"{key}_time")
    confirmed = st.checkbox("Revisei os alimentos e entendo que os valores são estimativas.", key=f"{key}_confirmed")
    if st.button("Salvar edição nutricional" if old else "Confirmar e salvar refeição", key=f"{key}_save", disabled=not(valid and confirmed)):
        try: details = meal_details(meal_type, items)
        except ValueError as error: st.error(str(error))
        else: save(client, day, meal_time.strftime("%H:%M:%S"), "meal", details, "Refeição confirmada e salva.", old=old, demo=demo)


def photo_meal(client, day, save, demo=False):
    with st.expander("Registrar refeição por foto", expanded=False):
        st.caption("Gemini via OpenRouter · teto de US$ 1/mês para todo o app, com saldo do administrador. Até 6 tentativas por conta/dia e 20 no app/dia. Sem recarga ou troca automática de modelo.")
        st.info("A foto do prato será enviada ao OpenRouter e ao Google Vertex para reconhecimento. O roteamento exige endpoint sem retenção (ZDR), mas os serviços ainda processam a imagem e metadados conforme suas políticas. Não envie rostos, documentos ou dados pessoais. Só os alimentos e valores confirmados são salvos no diário, não a foto.")
        st.link_button("Privacidade do OpenRouter", "https://openrouter.ai/privacy")
        if demo:
            st.caption("Envio de fotos desativado na demonstração. O registro manual permanece disponível.")
            return
        # Day is part of the draft key: a photo cannot silently transfer to another date.
        prefix = f"meal_photo_{day}"
        source = st.radio("Origem da foto", ["Escolher imagem", "Câmera"], key=prefix + "_source", horizontal=True)
        uploaded = st.file_uploader("Foto apenas do prato", type=["jpg", "jpeg", "png", "webp"], max_upload_size=8,
                                    key=prefix + "_upload") if source == "Escolher imagem" else st.camera_input("Fotografar prato", key=prefix + "_camera")
        consent = st.checkbox("Autorizo enviar somente esta foto do prato ao OpenRouter e ao Google e li o aviso acima.", key=prefix + "_consent_v2")
        adult = st.checkbox("Tenho 18 anos ou mais.", key=prefix + "_adult")
        if uploaded is None: return
        raw = uploaded.getvalue()
        digest = sha256(raw).hexdigest()[:16]
        draft_key = prefix + "_draft"
        draft = st.session_state.get(draft_key)
        if draft and draft["digest"] != digest:
            st.session_state.pop(draft_key, None)
            draft = None
        if st.button("Analisar foto", key=prefix + "_analyze", disabled=not(consent and adult)):
            try:
                jpeg = normalized_jpeg(raw)
                with st.spinner("Identificando alimentos e sugerindo porções…"):
                    proposal = recognize(client, jpeg, consent, adult)
                draft = {"digest": digest, "revision": uuid4().hex[:12], "proposal": proposal}
                st.session_state[draft_key] = draft
            except ValueError as error: st.error(str(error))
        if draft:
            review_meal(client, day, draft["proposal"], save, prefix + "_" + draft["revision"], demo=demo)
            if st.button("Descartar sugestão", key=prefix + "_discard"):
                st.session_state.pop(draft_key, None)
                # Clear all editor state, including confirmation, before starting over.
                for key in list(st.session_state):
                    if key.startswith(prefix + "_" + draft["revision"]): del st.session_state[key]
                st.rerun()
