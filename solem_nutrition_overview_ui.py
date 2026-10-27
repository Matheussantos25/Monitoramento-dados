"""Read-only daily nutrition highlight shared by all account profiles."""
from html import escape
import streamlit as st
from solem_meal_analysis import overview_nutrition


def nutrition_highlight(entries, day):
    result = overview_nutrition(entries, day)
    known = result is not None and result["known_items"] > 0
    def amount(key):
        if not known:
            return "—"
        return f"{result['totals'][key]:,.1f}".replace(",", "_").replace(".", ",").replace("_", ".")
    if result is None:
        status = "Diário indisponível · abra Saúde para tentar novamente."
    elif not result["meals"]:
        status = "Nenhuma refeição registrada hoje."
    elif not known:
        status = "Sem cálculo ainda · informe pesos e referências em Saúde."
    elif result["partial"]:
        status = "Total parcial · há alimentos ou refeições sem cálculo."
    else:
        status = f"{result['meals']} refeição(ões) somadas automaticamente."
    st.html(f'''<section class="nutrition-today" aria-label="Nutrição de hoje">
        <header><h2>Nutrição de hoje</h2><span>{day.strftime('%d/%m')}</span></header>
        <div class="nutrition-today__grid"><div><span>Calorias consumidas</span><strong>{amount('kcal')} <small>kcal</small></strong></div>
        <div><span>Proteínas consumidas</span><strong>{amount('protein_g')} <small>g</small></strong></div></div>
        <p>{escape(status)}</p><small>Estimativas das refeições registradas. Atualiza ao salvar, editar ou remover uma refeição.</small></section>''')
