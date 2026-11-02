from datetime import date, time
import os
import streamlit as st
import pandas as pd
from solem_charts import bar_card
from solem_health import now_local
from solem_progress import extras_of, record_date
from solem_languages import LANGUAGES, ACTIVITIES, SUBTITLES, is_language, language_session, language_summary, language_week, PERIODS, SESSION_TIMES, session_time, media_titles, period_bounds, language_period_summary, language_chart


def language_form(client, table, old=None, records=()):
    e = extras_of((old or {}).get("dados_extras"))
    key = "language_" + (str(old["id"]) if old else "new_"+str(st.session_state.get("language_form_generation",0)))
    choices = list(dict.fromkeys(LANGUAGES + ([e['idioma']] if e.get('idioma') else [])))
    language = st.selectbox("Idioma que estou aprendendo", choices, index=choices.index(e.get("idioma", "Inglês")), accept_new_options=True, key=key+"_language")
    activity = st.selectbox("Atividade", ACTIVITIES, index=ACTIVITIES.index(e.get("atividade_idioma", ACTIVITIES[0])), format_func=lambda v: "Série / anime / filme / vídeo" if v == ACTIVITIES[2] else v, key=key+"_activity")
    with st.form(key):
        c1,c2=st.columns(2)
        day=c1.date_input("Data da sessão", value=record_date(old["data"]) if old else now_local().date())
        clock_key=key+"_clock"
        st.session_state.setdefault(clock_key, str(old["horario"]) if old else now_local().strftime("%H:%M"))
        times=list(dict.fromkeys(SESSION_TIMES+[st.session_state[clock_key]]))
        at=c2.selectbox("Horário da sessão", times, key=clock_key, accept_new_options=True, filter_mode="prefix", help="Digite 22 para filtrar os horários das 22h. Também pode informar 22:17 ou 2217.")
        minutes=st.number_input("Tempo efetivo da sessão (min)", 1, 1440, int(old["duracao_min"]) if old else 20)
        if activity == ACTIVITIES[2]:
            titles=media_titles(records)
            if e.get("titulo") and e["titulo"] not in titles: titles.insert(0,e["titulo"])
            title=st.selectbox("Série, anime, filme ou vídeo", titles, index=titles.index(e["titulo"]) if e.get("titulo") in titles else None, accept_new_options=True, filter_mode="contains", key=key+"_media_title", placeholder="Escolha um título ou digite um novo", help="Sugestões do seu histórico, mais recentes primeiro. Um novo título fica disponível após salvar a sessão.") or ""
        else:
            title=st.text_input("Material ou baralho (opcional)", e.get("titulo", ""), max_chars=160)
        reviewed=added=episodes=0; audio=subtitles=""
        if activity == ACTIVITIES[0]:
            reviewed=st.number_input("Cards revisados", 0, 10000, int(e.get("cards_revisados",0)))
        if activity in ACTIVITIES[:2]:
            added=st.number_input("Cards adicionados ao Anki", 0, 10000, int(e.get("cards_adicionados",0)))
            st.caption("Registro manual. O Solem não acessa sua conta do Anki.")
        if activity == ACTIVITIES[2]:
            episodes=st.number_input("Episódios / vídeos vistos", 1, 100, max(1,int(e.get("episodios",1))))
            st.caption("No tempo acima, informe a soma dos minutos realmente assistidos. Ex.: 2 episódios de 25 min = 50 min; não multiplicaremos novamente.")
            audio=st.text_input("Idioma do áudio", e.get("idioma_audio") or language, max_chars=60)
            subtitles=st.selectbox("Legendas", SUBTITLES, index=SUBTITLES.index(e.get("legendas")) if e.get("legendas") in SUBTITLES else 0)
        notes=st.text_area("Observações (opcional)", e.get("observacoes", ""), max_chars=2000)
        if st.form_submit_button("Salvar alterações" if old else "Salvar sessão de idioma", use_container_width=True):
            try:
                value=language_session(day,session_time(at),language,activity,minutes,title=title,reviewed=reviewed,added=added,episodes=episodes,audio=audio,subtitles=subtitles,notes=notes,previous=old)
                query=client.table(table)
                result=(query.update(value).eq("id",int(old["id"])) if old else query.insert(value)).execute()
                if not result.data:
                    raise RuntimeError("unconfirmed")
            except ValueError as err:
                st.error(str(err))
            except Exception:
                st.error("Não foi possível confirmar a gravação. Atualize o histórico antes de tentar novamente.")
            else:
                st.session_state["solem_feedback"]="Sessão de idioma salva."
                st.session_state["language_form_generation"]=st.session_state.get("language_form_generation",0)+1
                st.rerun()


def language_page(records, client, table, demo=False):
    demo = demo or os.environ.get("SOLEM_DEMO") == "1"
    st.title("Idiomas")
    st.caption("Sua mente em movimento. Anki, séries e prática: acompanhe cada sessão, no seu ritmo.")
    rows=[r for r in records if is_language(r)]
    progress,register,history,vocabulary=st.tabs(["Progresso","Registrar sessão","Histórico e edição","Vocabulário → Anki"])
    with progress:
        options=["Todos"]+sorted({extras_of(r.get("dados_extras")).get("idioma","Inglês") for r in rows})
        a,b=st.columns([2,1])
        selected=a.selectbox("Idioma do painel",options)
        day=b.date_input("Data de referência", now_local().date(), max_value=now_local().date(), format="DD/MM/YYYY")
        period=st.segmented_control("Período do progresso",PERIODS,default="Últimos 7 dias",required=True,key="language_period",width="stretch")
        start,end=period_bounds(day,period)
        end=min(end,now_local().date())
        lang=None if selected=="Todos" else selected
        summary=language_period_summary(rows,start,end,lang)
        st.caption(f"{start:%d/%m/%Y} a {end:%d/%m/%Y} · {selected} · Todos os indicadores abaixo usam este intervalo.")
        with st.container(border=True):
            a,b=st.columns([2,1])
            a.metric("Tempo de estudo",f"{summary['minutes']:g} min")
            b.metric("Dias de prática",f"{summary['active_days']} / {(end-start).days+1}")
            st.caption(f"{summary['sessions']} sessões · {summary['minutes']/max(1,summary['active_days']):.0f} min por dia com prática")
        a,b=st.columns(2)
        a.metric("Revisão no Anki",f"{summary['review_minutes']:g} min",border=True)
        b.metric("Cards revisados",f"{summary['reviewed']:g}",border=True)
        a,b=st.columns(2)
        a.metric("Cards adicionados",f"{summary['added']:g}",border=True)
        b.metric("Episódios / vídeos",f"{summary['episodes']:g}",border=True,help="Também inclui filmes registrados como uma sessão de conteúdo.")
        if not summary['sessions']:
            st.info("Nenhuma sessão neste intervalo. Escolha outro período ou registre sua próxima prática.")
        chart=language_chart(rows,start,end,period,lang)
        unit="Horário" if period=="Dia" else "Mês" if period in ("Semestre","Ano") else "Dia"
        data=pd.DataFrame({unit:[x['label'] for x in chart],"Minutos":[x['minutes'] for x in chart]})
        bar_card(data,unit,"Minutos",title=f"Seu ritmo por {unit.lower()}",
                 unit="Minutos estudados · cada barra representa seu tempo registrado")
        st.caption("Tempo informado por você; não é uma avaliação de fluência.")
    with register:
        st.subheader("O que você praticou?")
        # Generation clears the successful form but never retries a submission on rerun.
        with st.container(key=f"language_generation_{st.session_state.get('language_form_generation',0)}"):
            language_form(client,table,records=rows)
    with history:
        filtered=sorted([r for r in rows if not lang or extras_of(r.get('dados_extras')).get('idioma')==lang],key=lambda r:(str(r['data']),str(r['horario']),int(r['id'])),reverse=True)
        if not filtered:
            st.info("Nenhuma sessão de idioma registrada ainda. Seu primeiro registro aparecerá aqui.")
        else:
            page=st.number_input("Página das sessões",1,max(1,(len(filtered)+9)//10),1)
            for row in filtered[(page-1)*10:page*10]:
                e=extras_of(row.get('dados_extras'))
                with st.expander(f"{record_date(row['data']).strftime('%d/%m/%Y')} · {str(row['horario'])[:5]} · {e['idioma']} · {e['atividade_idioma']} · {row['duracao_min']:g} min · #{row['id']}"):
                    if e.get('titulo'): st.write(e['titulo'])
                    if e.get('episodios'): st.caption(f"{e['episodios']} episódios/vídeos · Áudio: {e['idioma_audio']} · Legendas: {e['legendas']}")
                    language_form(client,table,row,records=rows)

    with vocabulary:
        from solem_vocabulary_ui import vocabulary_panel
        vocabulary_panel(demo=demo)
