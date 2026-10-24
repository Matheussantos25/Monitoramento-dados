"""Cumulative scale entry; individual-food weights remain the stored nutrition basis."""
from datetime import time
import streamlit as st
from solem_meal_analysis import catalog, cumulative_items, nutrition, meal_details, food_display_name
from solem_health import MEAL_TYPES, now_local

def cumulative_review(client, day, proposal, save, key, old=None, demo=False):
    from solem_meal_photo_ui import nutrient_metrics, reference_details
    table=catalog(); labels={food["id"]:food_display_name(food["name"]) for food in table}
    names={food["id"]:food["name"] for food in table}
    reference_details()
    previous=old.get("details",{}) if old else {}
    weighing=previous.get("weighing",{})
    source=proposal["items"]
    st.caption("Adicione os alimentos na mesma ordem em que foram colocados no prato. Não zere a balança entre eles. Se retirar comida ou zerar novamente, use o modo individual.")
    baseline=st.number_input("Leitura inicial: prato vazio (g) — 0 se usou tara",0.0,10000.0,
                             float(weighing.get("baseline_g",0)),step=1.0,key=f"{key}_baseline")
    items=[]; readings=[]
    old_readings=weighing.get("readings_g",[])
    reconstructed=float(weighing.get("baseline_g",0))
    for index,item in enumerate(source):
        reconstructed+=float(item["grams"])
        with st.container(border=True):
            st.markdown(f"**{index+1}. {food_display_name(item['name'])}**")
            chosen=st.selectbox("Referência nutricional / preparo",[""]+list(labels),
                index=([""]+list(labels)).index(item.get("food_id","") if item.get("food_id","") in labels else ""),
                format_func=lambda value:labels.get(value,"Sem correspondência — não calcular"),key=f"{key}_food_{index}")
            reading=st.number_input("Leitura da balança após este alimento (g)",0.0,34000.0,
                float(old_readings[index] if len(old_readings)==len(source) else reconstructed),1.0,key=f"{key}_reading_{index}")
            items.append({**item,"food_id":chosen});readings.append(reading)
    added=st.multiselect("Adicionar alimentos na ordem da pesagem",list(labels),format_func=labels.get,key=f"{key}_added")
    for index,food_id in enumerate(added):
        # Removing/reordering an earlier addition invalidates subsequent readings.
        order="_".join(added[:index+1])
        reading=st.number_input(f"{len(source)+index+1}. Balança após {labels[food_id]} (g)",0.0,34000.0,0.0,1.0,
                                key=f"{key}_reading_extra_{order}")
        items.append(dict(name=names[food_id],food_id=food_id,grams=0));readings.append(reading)
    st.caption("Ao remover ou trocar a ordem de uma adição, confira e preencha novamente as leituras seguintes. Para remover alimentos de uma refeição já salva, use o modo individual.")
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
    old_type=previous.get("tipo_refeicao","Almoço")
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
