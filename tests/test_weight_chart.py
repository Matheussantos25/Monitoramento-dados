from datetime import date
from streamlit.testing.v1 import AppTest
from solem_weight_chart import weight_series


def test_sparse_dates_exact_weights_and_single_point_scale():
    points = [(date(2026,11,5),68.6), (date(2026,10,1),68.05)]
    data, bounds = weight_series(points)
    assert [(x['Data'],x['Peso']) for x in data] == [('2026-10-01T00:00:00',68.05),('2026-11-05T00:00:00',68.6)]
    assert [x['Ultima'] for x in data] == [False, True]
    assert len(points) == 2 and points[0][0] == date(2026,11,5)
    assert bounds[0] < 68.05 < 68.6 < bounds[1]
    one, bounds = weight_series([(date(2026,11,5),68.6)])
    assert one[0]['Peso'] == 68.6 and bounds[1]-bounds[0] >= 1
    assert weight_series([])[0] == []


def test_weight_panel_empty_single_and_history_render_without_writes():
    for points in ['[]','[(date(2026,11,5),68.6)]','[(date(2026,11,1),68.1),(date(2026,11,5),68.6)]']:
        app=AppTest.from_string('from datetime import date\nfrom solem_weight_chart import weight_card\nweight_card('+points+')').run()
        assert not app.exception
        if points != '[]':
            assert next(x for x in app.metric if x.label=='Último registro').value == '68,6 kg'
            assert len(app.get('vega_lite_chart')) == 1
