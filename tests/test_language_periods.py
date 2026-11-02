from datetime import date
from copy import deepcopy
import pytest
from streamlit.testing.v1 import AppTest
from solem_languages import *


def row(identity,day,minutes=20,language="Inglês",title=""):
    return dict(id=identity,**language_session(day,"22:17",language,ACTIVITIES[2] if title else ACTIVITIES[0],minutes,
        title=title,episodes=1 if title else 0,audio=language,subtitles=SUBTITLES[0],reviewed=10))


def test_calendar_boundaries_and_leap_year():
    assert period_bounds(date(2024,2,20),"Mês")== (date(2024,2,1),date(2024,2,29))
    assert period_bounds(date(2026,1,3),"Últimos 7 dias")== (date(2025,12,28),date(2026,1,3))
    assert period_bounds(date(2026,6,30),"Semestre")== (date(2026,1,1),date(2026,6,30))
    assert period_bounds(date(2026,7,1),"Semestre")== (date(2026,7,1),date(2026,12,31))
    assert period_bounds(date(2026,11,2),"Ano")== (date(2026,1,1),date(2026,12,31))


def test_every_metric_and_chart_share_interval_language_and_deduplication():
    rows=[row(1,date(2025,12,31),10),row(2,date(2026,1,1),30),row(3,date(2026,1,3),40,title="Film"),row(4,date(2026,1,3),90,"Espanhol"),row(5,date(2026,1,4),50)]
    original=deepcopy(rows)
    start,end=period_bounds(date(2026,1,3),"Últimos 7 dias")
    totals=language_period_summary(rows+[rows[0]],start,end,"Inglês")
    assert totals==dict(minutes=80,review_minutes=40,reviewed=20,added=0,episodes=1,sessions=3,active_days=3)
    chart=language_chart(rows+[rows[0]],start,end,"Últimos 7 dias","Inglês")
    assert sum(x['minutes'] for x in chart)==totals['minutes'] and len(chart)==7
    assert chart[0]['label']=='28/12' and chart[-1]['label']=='03/01'
    assert rows==original
    yearly=language_chart(rows,date(2026,1,1),date(2026,12,31),"Ano","Inglês")
    assert len(yearly)==12 and yearly[0]['minutes']==120
    hourly=language_chart(rows,date(2026,1,3),date(2026,1,3),"Dia","Inglês")
    assert len(hourly)==24 and hourly[22]['minutes']==40


@pytest.mark.parametrize('value,expected',[('22','22:00'),('2217','22:17'),('9:03','09:03'),('0030','00:30'),('23:59','23:59'),('08:15:30','08:15:30')])
def test_free_typing_time(value,expected):
    assert session_time(value)==expected


@pytest.mark.parametrize('value',['24','24:00','22:60','abc','',None,'-1'])
def test_invalid_time_not_saved(value):
    with pytest.raises(ValueError):session_time(value)


def test_titles_are_personal_media_only_recent_and_deduplicated():
    rows=[row(1,date(2026,1,1),title="Frieren"),row(2,date(2026,1,2),title=" frieren "),row(3,date(2026,1,3),title="Arrival"),row(4,date(2026,1,4))]
    rows[-1]['dados_extras']['titulo']='Anki deck'
    assert media_titles(rows)==['Arrival','frieren']
    assert media_titles([])==[]


def test_dashboard_filter_and_searchable_form_without_mutating_history():
    source='''
import streamlit as st
from datetime import date
from solem_languages_ui import language_page
from solem_languages import language_session
class Client: pass
rows=[dict(id=1,**language_session(date(2026,1,1),'22:17','Inglês','Revisão no Anki',20,reviewed=30)),dict(id=2,**language_session(date(2026,1,2),'23:00','Inglês','Série / vídeo',40,title='Frieren',episodes=2,audio='Japonês',subtitles='No idioma estudado'))]
language_page(rows,Client(),'test',demo=True)
'''
    app=AppTest.from_string(source,default_timeout=40).run()
    next(x for x in app.date_input if x.label=='Data de referência').set_value(date(2026,1,2)).run()
    assert next(m for m in app.metric if m.label=='Tempo de estudo').value=='60 min'
    app.segmented_control(key='language_period').set_value('Dia').run()
    assert next(m for m in app.metric if m.label=='Tempo de estudo').value=='40 min'
    app.segmented_control(key='language_period').set_value('Ano').run()
    assert next(m for m in app.metric if m.label=='Tempo de estudo').value=='60 min'
    app.selectbox(key='language_new_0_activity').set_value(ACTIVITIES[2]).run()
    titles=next(x for x in app.selectbox if x.label=='Série, anime, filme ou vídeo')
    assert 'Frieren' in titles.options
    assert next(x for x in app.selectbox if x.label=='Horário da sessão').proto.filter_mode != 0
    assert not app.exception
