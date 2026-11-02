"""Shared, grid-free presentation. Chart data and axis ranges stay unchanged."""
import plotly.graph_objects as go
import streamlit as st
from textwrap import wrap

PALETTE = ["#83DCFF", "#BBA6D9", "#F0BE7B", "#8AAEE0", "#ED9DAE"]


def clean_figure(figure):
    fig = go.Figure(figure)
    horizontal = any(t.type == "bar" and t.orientation == "h" for t in fig.data)
    count = max((len(t.y if horizontal else t.x) for t in fig.data
                 if (t.y if horizontal else t.x) is not None), default=0)
    fig.update_layout(
        template="none", height=min(480, max(260, count * 35 + 65)) if horizontal else 290,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#DCEEFF", size=12),
        margin=dict(l=10, r=35, t=35, b=35),
        bargap=0.38, barcornerradius=7,
        legend=dict(orientation="h", y=1.12, x=0, title_text=""),
        hoverlabel=dict(bgcolor="#15243A", font_color="#EAF4FF"),
        coloraxis=dict(colorscale=[[0,"#36779B"],[1,"#83DCFF"]], showscale=False),
        transition_duration=0,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showline=False, ticks="",
                     tickangle=0, nticks=6, dtick=None, automargin=True, tickfont_color="#A9BBD1")
    fig.update_yaxes(showgrid=False, zeroline=False, showline=False, ticks="",
                     automargin=True, tickfont_color="#A9BBD1")
    if not horizontal:
        fig.update_yaxes(nticks=4)
    elif fig.data:
        labels=list(dict.fromkeys(str(label) for trace in fig.data for label in (trace.y if trace.y is not None else [])))
        fig.update_yaxes(tickvals=labels, ticktext=["<br>".join(wrap(label,26)[:2]) + ("…" if len(wrap(label,26))>2 else "") for label in labels], tickfont_size=11)
    for i, trace in enumerate(fig.data):
        color = PALETTE[i % len(PALETTE)]
        if trace.type == "bar":
            if not trace.marker.coloraxis:
                trace.update(marker_color=color)
            trace.update(marker_line_width=0, textfont_color="#DCEEFF", textfont_size=12,
                         cliponaxis=False)
            if count > 16:
                trace.update(textposition="none")
        elif trace.type == "scatter":
            trace.update(line_color=color, line_width=2.5, marker_color=color, marker_size=6)
    return fig


def plotly_card(figure, *, card=True, key=None, **kwargs):
    config = {"displayModeBar": False, "scrollZoom": False, **kwargs.pop("config", {})}
    def draw():
        st.plotly_chart(clean_figure(figure), use_container_width=True, theme=None,
                        config=config, key=key)
        values=[]
        for trace in figure.data:
            horizontal=trace.type=="bar" and trace.orientation=="h"
            categories=trace.y if horizontal else trace.x
            numbers=trace.x if horizontal else trace.y
            if categories is None or numbers is None: continue
            for category,value in zip(categories,numbers):
                values.append({"Série":trace.name or "Registros","Data / categoria":str(category),"Valor":value})
        if values:
            with st.expander("Ver valores do gráfico"):
                st.dataframe(values,hide_index=True)
    if card:
        with st.container(border=True):
            draw()
    else:
        draw()


def bar_card(data, x, y, *, title, unit="", key=None):
    """Compact chronological bars; zero markers never imply nonzero activity."""
    count = len(data)
    encoding = {
        "x":{"field":x,"type":"ordinal","sort":None,
             "axis":{"title":None,"labelAngle":0,"labelOverlap":"greedy","labelPadding":12},
             "scale":{"paddingInner":0.45,"paddingOuter":0.35}},
        "y":{"field":y,"type":"quantitative","scale":{"domainMin":0,"nice":True},
             "axis":None if count<=12 else {"title":None,"tickCount":3,"labelPadding":10}},
        "tooltip":[{"field":x,"type":"nominal"},{"field":y,"type":"quantitative","title":y}],
    }
    layers=[{"mark":{"type":"bar","color":{"gradient":"linear","x1":0,"y1":1,"x2":0,"y2":0,
                "stops":[{"offset":0,"color":"#206284"},{"offset":1,"color":"#83DCFF"}]},
                "size":32 if count<=12 else 8,"cornerRadiusTopLeft":7,"cornerRadiusTopRight":7,
                "cornerRadiusBottomLeft":3,"cornerRadiusBottomRight":3},"encoding":encoding},
            {"transform":[{"filter":{"field":y,"equal":0}}],
             "mark":{"type":"tick","orient":"horizontal","size":12,"thickness":3,"color":"#34465E"},
             "encoding":encoding}]
    if count<=12:
        layers.append({"transform":[{"filter":{"field":y,"gt":0}}],
                       "mark":{"type":"text","dy":-12,"color":"#DCEEFF","fontSize":12,"fontWeight":600},
                       "encoding":{"x":encoding["x"],"y":encoding["y"],
                                   "text":{"field":y,"type":"quantitative","format":"~g"}}})
    with st.container(border=True):
        st.markdown(f"**{title}**")
        if unit: st.caption(unit)
        st.vega_lite_chart(data,{
            "height":200,"padding":{"top":22,"bottom":4,"left":0,"right":8},
            "background":"transparent","layer":layers,
            "config":{"view":{"stroke":None},"axis":{"grid":False,"domain":False,"ticks":False,
                       "labelColor":"#A9BBD1","labelFontSize":12,"labelFont":"sans-serif"}},
        },use_container_width=True,theme=None,key=key)
        with st.expander("Ver valores do gráfico"):
            st.dataframe(data,hide_index=True)
