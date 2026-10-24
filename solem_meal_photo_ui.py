"""Local nutrition display and editing for existing meal records."""
import streamlit as st
from solem_health import MEAL_TYPES, now_local
from solem_meal_analysis import catalog, nutrition, meal_details, day_nutrition, food_display_name


def reference_details():
    with st.expander("Referências nutricionais e preparo"):
        st.caption("Os nomes são simplificados. O cálculo continua usando estas referências específicas; preparo e ingredientes podem mudar os valores.")
        for food in catalog():
            st.write(f"{food_display_name(food['name'])} — {food['name']}")


def nutrient_metrics(result):
    title = "Estimativa parcial" if not result.get("complete", True) else "Estimativa nutricional"
    st.caption(title + " · calculada pelo peso informado e pela referência nutricional. Óleo, molhos e preparo podem alterar os valores.")
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
            st.caption(f"{result['counted']} de {len(meals)} refeição(ões) com cálculo. Valores parciais quando faltam pesos ou referências nutricionais.")
    else:
        st.info("Calorias e proteínas do dia: sem cálculo ainda. Registre alimentos com peso; refeições antigas sem porções não são tratadas como zero.")


def review_meal(client, day, proposal, save, key, old=None, demo=False, weighed=False):
    if old is None:
        from solem_voice_ui import meal_voice_draft
        proposal, key = meal_voice_draft(proposal, key)
    # New meals use scale readings; editing keeps the saved interpretation.
    cumulative_saved=old is None or old.get("details",{}).get("weighing",{}).get("mode")=="cumulative"
    mode=st.radio("Como vai informar os pesos?",["Peso individual de cada alimento","Peso acumulado da balança"],
                  index=int(cumulative_saved),key=f"{key}_weighing_mode")
    st.caption("Os modos têm rascunhos separados. Salve antes de trocar de modo se quiser manter as alterações.")
    if mode=="Peso acumulado da balança":
        from solem_cumulative_meal_ui import cumulative_review
        cumulative_review(client,day,proposal,save,f"{key}_cum",old,demo)
        return
    table = catalog()
    labels = {food["id"]: food_display_name(food["name"]) for food in table}
    names = {food["id"]: food["name"] for food in table}
    reference_details()
    source_items = proposal["items"]
    items = []
    weighed = weighed or bool(old and old.get("details", {}).get("input_method") == "weighed")
    st.markdown("#### Refeição com balança" if weighed else "#### Confira seu prato")
    st.caption("Zere a balança com o prato vazio (tara). Informe só o peso consumido de cada alimento, sem ossos ou cascas não consumidas. Escolha a referência do mesmo preparo: cru ou cozido. Inclua óleo e molhos separadamente; 0 g deixa o alimento sem cálculo.")
    for index, item in enumerate(source_items):
        with st.container(border=True):
            display_name = food_display_name(item["name"])
            name = st.text_input("Alimento", value=display_name, max_chars=80, key=f"{key}_name_{index}")
            if name == display_name: name = item["name"]
            chosen = st.selectbox("Referência nutricional / preparo", [""] + list(labels),
                index=([""] + list(labels)).index(item.get("food_id", "") if item.get("food_id", "") in labels else ""),
                format_func=lambda food_id: labels.get(food_id, "Sem correspondência — não calcular"), key=f"{key}_food_{index}")
            grams = st.number_input("Peso consumido (g)", min_value=0.0, max_value=2000.0,
                value=float(item["grams"]), step=1.0, key=f"{key}_grams_{index}")
            include = st.checkbox("Incluir este alimento", value=True, key=f"{key}_include_{index}")
            if chosen:
                food = next(food for food in table if food["id"] == chosen)
                st.link_button("Consultar fonte USDA", food["source_url"])
            if include:
                entry = {"name": name, "food_id": chosen, "grams": grams, "confidence": item.get("confidence", "low")}
                items.append(entry)
                if name.strip() and chosen and grams:
                    values = nutrition([entry])["totals"]
                    st.caption(f"Este alimento: {values['kcal']:.1f} kcal · {values['protein_g']:.1f} g de proteína")
    # Add missing ingredients without another AI request (also supports manual corrections).
    added = st.multiselect("Adicionar alimentos à refeição", list(labels), format_func=labels.get, key=f"{key}_added")
    for food_id in added:
        grams = st.number_input(f"Peso de {labels[food_id]} (g)", 0.0, 2000.0, 0.0, 1.0, key=f"{key}_extra_{food_id}")
        entry = {"name": names[food_id], "food_id": food_id, "grams": grams, "confidence": "low"}
        items.append(entry)
        if grams:
            values = nutrition([entry])["totals"]
            st.caption(f"{labels[food_id]}: {values['kcal']:.1f} kcal · {values['protein_g']:.1f} g de proteína")
    st.caption("Alimento sem referência compatível? Use o registro simples, sem estimar valores de outro alimento.")
    valid = False
    try:
        result = nutrition(items)
        st.markdown("**Total da refeição · soma dos alimentos**")
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
        try: details = meal_details(meal_type, items, weighed=weighed)
        except ValueError as error: st.error(str(error))
        else: save(client, day, meal_time.strftime("%H:%M:%S"), "meal", details, "Refeição confirmada e salva.", old=old, demo=demo)
