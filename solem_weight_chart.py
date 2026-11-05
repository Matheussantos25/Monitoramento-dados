"""Read-only weight presentation using the same visual language as Idiomas."""
import streamlit as st


def weight_series(points):
    ordered = sorted(points)
    if not ordered:
        return [], [0, 1]
    values = [kg for _, kg in ordered]
    padding = max(0.5, (max(values) - min(values)) * 0.2)
    domain = [max(0, min(values) - padding), max(values) + padding]
    # An explicit local time avoids JavaScript interpreting date-only ISO as UTC
    # and displaying the previous calendar day west of Greenwich.
    return [dict(Data=day.isoformat()+"T00:00:00", Peso=kg, Base=domain[0], Ultima=index==len(ordered)-1)
            for index, (day, kg) in enumerate(ordered)], domain


def weight_card(points):
    points = sorted(points)
    data, domain = weight_series(points)
    with st.container(border=True):
        st.markdown("**Evolução do peso corporal**")
        if not data:
            st.info("Registre seu peso para começar a acompanhar a evolução.")
            return
        latest, first = data[-1], data[0]
        left, right = st.columns(2)
        left.metric("Último registro", f"{latest['Peso']:.1f} kg".replace('.', ','))
        difference = latest['Peso'] - first['Peso']
        right.metric("Variação no período", (f"{difference:+.1f} kg".replace('.', ',')
                     if len(data) > 1 else "—"))
        st.caption(f"{len(data)} medidas · {points[0][0]:%d/%m/%Y} a {points[-1][0]:%d/%m/%Y}")
        encoding = {
            "x": {"field": "Data", "type": "temporal", "axis": {
                "title": None, "format": "%d/%m", "tickCount": 4,
                "labelAngle": 0, "labelOverlap": True, "labelPadding": 12}},
            "y": {"field": "Peso", "type": "quantitative",
                  "scale": {"domain": domain, "zero": False, "nice": False},
                  "axis": {"title": None, "tickCount": 3, "format": ".1f", "labelPadding": 10}},
            "tooltip": [{"field": "Data", "type": "temporal", "format": "%d/%m/%Y"},
                        {"field": "Peso", "type": "quantitative", "title": "Peso (kg)", "format": ".1f"}],
        }
        st.vega_lite_chart(data, {
            "height": 220, "background": "transparent", "padding": {"top": 16, "right": 16},
            "encoding": encoding,
            "layer": [
                {"mark": {"type": "area", "color": {"gradient": "linear", "x1": 0, "y1": 0, "x2": 0, "y2": 1,
                    "stops": [{"offset": 0, "color": "#206284"}, {"offset": 1, "color": "#0B1422"}]}, "opacity": 0.4},
                 "encoding": {"y2": {"field": "Base"}}},
                {"mark": {"type": "line", "color": "#83DCFF", "strokeWidth": 3,
                          "point": {"filled": True, "size": 35}}},
                {"transform": [{"filter": {"field": "Ultima", "equal": True}}],
                 "mark": {"type": "point", "filled": True, "size": 110, "color": "#83DCFF",
                          "stroke": "#DCEEFF", "strokeWidth": 2}},
            ],
            "config": {"view": {"stroke": None}, "axis": {"grid": False, "domain": False, "ticks": False,
                "labelColor": "#A9BBD1", "labelFontSize": 12, "labelFont": "sans-serif"}},
        }, use_container_width=True, theme=None, key="private_weight_chart")
        st.caption("Valores em kg · a escala acompanha suas medidas. A linha liga apenas os dias registrados.")
        if len(data) == 1:
            st.caption("Sua primeira medida está registrada. A próxima formará a linha de evolução.")
        with st.expander("Ver valores do gráfico"):
            st.dataframe([{"Data": day.strftime("%d/%m/%Y"), "Peso (kg)": kg} for day, kg in sorted(points)], hide_index=True)
