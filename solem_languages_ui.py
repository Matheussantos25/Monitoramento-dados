from datetime import date, time
import streamlit as st
import pandas as pd
from solem_health import now_local
from solem_progress import extras_of, record_date
from solem_languages import LANGUAGES, ACTIVITIES, SUBTITLES, is_language, language_session, language_summary, language_week


def language_form(client, table, old=None):
    e = extras_of((old or {}).get("dados_extras"))
    key = "language_" + (str(old["id"]) if old else "new_"+str(st.session_state.get("language_form_generation",0)))
    choices = list(dict.fromkeys(LANGUAGES + ([e['idioma']] if e.get('idioma') else [])))
    language = st.selectbox("Idioma que estou aprendendo", choices, index=choices.index(e.get("idioma", "Inglês")), accept_new_options=True, key=key+"_language")
    activity = st.selectbox("Atividade", ACTIVITIES, index=ACTIVITIES.index(e.get("atividade_idioma", ACTIVITIES[0])), key=key+"_activity")
    with st.form(key):
        c1,c2=st.columns(2)
        day=c1.date_input("Data da sessão", value=record_date(old["data"]) if old else now_local().date())
        st.session_state.setdefault(key+"_time", time.fromisoformat(str(old["horario"])) if old else now_local().time().replace(second=0,microsecond=0))
        at=c2.time_input("Horário da sessão", key=key+"_time", step=60)
        minutes=st.number_input("Tempo efetivo da sessão (min)", 1, 1440, int(old["duracao_min"]) if old else 20)
        title=st.text_input("Nome da série / vídeo" if activity == ACTIVITIES[2] else "Material ou baralho (opcional)", e.get("titulo", ""), max_chars=160)
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
                value=language_session(day,at,language,activity,minutes,title=title,reviewed=reviewed,added=added,episodes=episodes,audio=audio,subtitles=subtitles,notes=notes,previous=old)
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
    st.title("Idiomas")
    st.caption("Sua mente em movimento. Anki, séries e prática: acompanhe cada sessão, no seu ritmo.")
    rows=[r for r in records if is_language(r)]
    progress,register,history,vocabulary=st.tabs(["Progresso","Registrar sessão","Histórico e edição","Vocabulário → Anki"])
    with progress:
        options=["Todos"]+sorted({extras_of(r.get("dados_extras")).get("idioma","Inglês") for r in rows})
        selected=st.selectbox("Idioma do painel",options)
        day=st.date_input("Dia do progresso", now_local().date())
        lang=None if selected=="Todos" else selected
        summary=language_summary(rows,day,lang)
        a,b=st.columns(2)
        a.metric("Tempo de estudo",f"{summary['minutes']:g} min")
        b.metric("Revisão no Anki",f"{summary['review_minutes']:g} min")
        a,b,c=st.columns(3)
        a.metric("Cards revisados",f"{summary['reviewed']:g}")
        b.metric("Cards adicionados",f"{summary['added']:g}")
        c.metric("Episódios / vídeos",f"{summary['episodes']:g}")
        with st.expander("Últimos 7 dias",expanded=True):
            week=language_week(rows,day,lang)
            data=pd.DataFrame({"Dia":[x['day'].isoformat() for x in week],"Minutos":[x['minutes'] for x in week]})
            st.bar_chart(data,x="Dia",y="Minutos",color="#83DCFF",height=180)
            st.caption("Tempo informado por você; não é uma avaliação de fluência.")
    with register:
        st.subheader("O que você praticou?")
        # Generation clears the successful form but never retries a submission on rerun.
        with st.container(key=f"language_generation_{st.session_state.get('language_form_generation',0)}"):
            language_form(client,table)
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
                    language_form(client,table,row)

    with vocabulary:
        from solem_vocabulary_ui import vocabulary_panel
        vocabulary_panel(demo=demo)
