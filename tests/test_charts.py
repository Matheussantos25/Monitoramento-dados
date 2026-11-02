from copy import deepcopy
import plotly.graph_objects as go
from solem_charts import clean_figure


def test_shared_style_preserves_all_series_values_ranges_and_hover():
    fig=go.Figure([
        go.Bar(x=['01/11','02/11'],y=[30,50],name='Minutos',hovertemplate='%{y} min'),
        go.Bar(x=['01/11','02/11'],y=[90,120],name='Segundos',customdata=['a','b']),
    ])
    fig.update_layout(barmode='group',yaxis_range=[0,150],xaxis_range=[-.5,1.5])
    original=deepcopy(fig.to_dict())
    styled=clean_figure(fig)
    assert fig.to_dict()==original
    for before,after in zip(fig.data,styled.data):
        assert (before.x,before.y,before.name,before.customdata,before.hovertemplate)==(after.x,after.y,after.name,after.customdata,after.hovertemplate)
    assert styled.layout.yaxis.range==(0,150)
    assert styled.layout.xaxis.range==(-.5,1.5)
    assert styled.layout.barmode=='group'
    assert styled.data[0].marker.color!=styled.data[1].marker.color
    assert styled.layout.xaxis.showgrid is False and styled.layout.yaxis.showgrid is False


def test_weight_and_long_topic_labels_keep_exact_data():
    weight=go.Figure(go.Scatter(x=['2026-11-01','2026-11-02'],y=[68.1,68.05],mode='lines+markers'))
    assert clean_figure(weight).data[0].y==(68.1,68.05)
    label='Matemática - Probabilidade condicional e interpretação de gráficos'
    topic=go.Figure(go.Bar(x=[75.5],y=[label],orientation='h',hovertemplate='%{y}: %{x}%'))
    result=clean_figure(topic)
    assert result.data[0].x==(75.5,) and result.data[0].y==(label,)
    assert result.data[0].hovertemplate==topic.data[0].hovertemplate
    assert '<br>' in result.layout.yaxis.ticktext[0]
