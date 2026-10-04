"""Local nutrition display and editing for existing meal records."""
import streamlit as st
from solem_health import MEAL_TYPES, now_local
from solem_meal_analysis import catalog, nutrition, meal_details, day_nutrition


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
