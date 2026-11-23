"""Cumulative scale entry; individual-food weights remain the stored nutrition basis."""
from datetime import time
import json
import streamlit as st
from solem_meal_analysis import catalog, cumulative_items, nutrition, meal_details, food_display_name, meal_choices, food_sort_key
from solem_health import MEAL_TYPES, now_local

def cumulative_review(client, day, proposal, save, key, old=None, demo=False, entries=()):
    from solem_meal_photo_ui import nutrient_metrics, reference_details, occasional_shortcut
    table=sorted(catalog(), key=lambda food: food_sort_key(food.get("display_name", food["name"])))
    labels={food["id"]:food_display_name(food["name"]) for food in table}
    choices = meal_choices(table, entries)
    reference_details()
    previous=old.get("details",{}) if old else {}
    weighing=proposal.get("voice_weighing") or previous.get("weighing",{})
    source=proposal["items"]
    signature=json.dumps([source,weighing],sort_keys=True,ensure_ascii=False)
    signature_key=f"{key}_source_signature"
    if signature_key in st.session_state and st.session_state[signature_key] != signature:
        # A successful edit changed the source. Reopen that version, not the old draft order.
        for state_key in list(st.session_state):
            if state_key.startswith(f"{key}_"):
                del st.session_state[state_key]
    st.session_state[signature_key]=signature
    st.caption("Adicione os alimentos na mesma ordem em que foram colocados no prato. Não zere a balança entre eles. Se retirar comida ou zerar novamente, use o modo individual.")
    def unconfirm_baseline():
        st.session_state[f"{key}_confirmed"] = False

    baseline=st.number_input("Leitura inicial: prato vazio (g) — 0 se usou tara",0.0,10000.0,
                             float(weighing.get("baseline_g",0)),step=1.0,key=f"{key}_baseline",on_change=unconfirm_baseline)
    from solem_food_order import sync_order, food_order
    occasional_shortcut(table, key)
    added=st.multiselect("Adicionar alimentos na ordem da pesagem",list(choices),format_func=lambda value: choices[value][0],key=f"{key}_added",
                         placeholder="Digite o nome ou a primeira letra", filter_mode="contains", help="Opções de A a Z. Corrija a sequência no controle de ordem abaixo.")
    rows = {f"source:{i}": dict(item) for i, item in enumerate(source)}
    rows.update({f"added:{choice}": dict(name=choices[choice][1],food_id=choices[choice][2],grams=0) for choice in added})
    old_readings=weighing.get("readings_g",[])
    reconstructed=float(weighing.get("baseline_g",0))
    defaults={}
    for i,item in enumerate(source):
        reconstructed+=float(item["grams"])
        defaults[f"source:{i}"]=old_readings[i] if len(old_readings)==len(source) else reconstructed
    order=sync_order(st.session_state,key,list(rows),defaults)
    food_order(key,{token:food_display_name(item["name"]) for token,item in rows.items()})

    def unconfirm():
        st.session_state[f"{key}_confirmed"] = False

    items=[]; readings=[]
    for index,token in enumerate(order):
        item=rows[token]
        name=food_display_name(item["name"])
        if token.startswith("source:"):
            chosen=st.selectbox(f"Referência de {name} / preparo",[""]+list(labels),
                index=([""]+list(labels)).index(item.get("food_id","") if item.get("food_id","") in labels else ""),
                format_func=lambda value:labels.get(value,"Sem correspondência — não calcular"),
                filter_mode="contains",key=f"{key}_reference_{token}",on_change=unconfirm)
            item={**item,"food_id":chosen}
        reading=st.number_input(f"{index+1}. Balança após {name} (g)",0.0,34000.0,step=1.0,
                                key=f"{key}_slot_reading_{index}",on_change=unconfirm)
        items.append(item);readings.append(reading)
    st.caption("Trocar a ordem recalcula as porções sem alterar as leituras. Remover uma seleção limpa as leituras a partir daquela posição. Nada muda na refeição salva até você confirmar e salvar.")
    valid=False
    try:
        calculated=cumulative_items(items,baseline,readings)
        result=nutrition(calculated)
        previous_reading=baseline
        for index,(item,reading) in enumerate(zip(calculated,readings)):
            values=nutrition([item])
            st.write(f"{index+1}. {food_display_name(item['name'])}: {reading:g} − {previous_reading:g} = **{item['grams']:g} g**")
            if values["complete"]:
                st.caption(f"{values['totals']['kcal']:.1f} kcal · {values['totals']['protein_g']:.1f} g de proteína")
            previous_reading=reading
        st.markdown("**Total da refeição · soma dos alimentos, sem o prato**")
        nutrient_metrics(result)
        valid=True
    except ValueError as error: st.info(str(error))
    old_type=proposal.get('voice_type') or previous.get("tipo_refeicao","Almoço")
    types=list(dict.fromkeys([*MEAL_TYPES,old_type]))
    kind=st.selectbox("Refeição",types,index=types.index(old_type),key=f"{key}_type")
    when=time.fromisoformat(str(old["logged_at"])) if old else now_local().time().replace(second=0,microsecond=0)
    logged=st.time_input("Horário",value=when,key=f"{key}_time")
    confirmed=st.checkbox("Conferi a ordem, as leituras e os pesos calculados.",key=f"{key}_confirmed")
    if st.button("Salvar edição nutricional" if old else "Confirmar e salvar refeição",key=f"{key}_save",disabled=not(valid and confirmed)):
        try:
            details=meal_details(kind,items,weighed=True,weighing=dict(baseline_g=baseline,readings_g=readings))
            save(client,day,logged.strftime("%H:%M:%S"),"meal",details,"Refeição salva com pesos calculados por diferença.",old=old,demo=demo)
        except ValueError as error: st.error(str(error))
