"""Language sessions use the existing owner-scoped activity store, without migrating history."""
from datetime import date, time, timedelta
from solem_progress import extras_of, number, record_date

LANGUAGES = ["Inglês", "Espanhol", "Francês", "Italiano", "Alemão", "Japonês", "Coreano", "Mandarim"]
ACTIVITIES = ["Revisão no Anki", "Criação de cards", "Série / vídeo", "Leitura", "Conversação", "Escuta", "Escrita", "Aula / prática"]
SUBTITLES = ["No idioma estudado", "Em português", "Sem legenda", "Outro idioma"]


def is_language(row):
    return row.get("grupo_muscular") == "Estudos" and extras_of(row.get("dados_extras")).get("language_schema") == 1


def language_session(day, at, language, activity, minutes, *, title="", reviewed=0, added=0,
                     episodes=0, audio="", subtitles="", notes="", previous=None):
    date.fromisoformat(str(day)); time.fromisoformat(str(at))
    language, title, notes = language.strip(), title.strip(), notes.strip()
    if not 1 <= len(language) <= 60 or activity not in ACTIVITIES:
        raise ValueError("Informe o idioma e a atividade.")
    if not isinstance(minutes, int) or not 1 <= minutes <= 1440:
        raise ValueError("Informe o tempo efetivo da sessão, entre 1 e 1.440 minutos.")
    if len(title) > 160 or len(notes) > 2000:
        raise ValueError("Use até 160 caracteres no título e 2.000 nas observações.")
    if any(not isinstance(n, int) or not 0 <= n <= 10000 for n in (reviewed, added, episodes)):
        raise ValueError("Use contagens inteiras entre 0 e 10.000.")
    if activity == "Série / vídeo" and (not title or not 1 <= episodes <= 100 or not audio.strip() or subtitles not in SUBTITLES):
        raise ValueError("Informe título, quantidade de episódios/vídeos, idioma do áudio e legendas.")
    # Only fields belonging to the current activity survive a change of type.
    extra = dict(extras_of((previous or {}).get("dados_extras")))
    extra.update(language_schema=1, idioma=language, atividade_idioma=activity, titulo=title,
                 cards_revisados=reviewed if activity == ACTIVITIES[0] else 0,
                 cards_adicionados=added if activity in ACTIVITIES[:2] else 0,
                 episodios=episodes if activity == ACTIVITIES[2] else 0,
                 idioma_audio=audio.strip()[:60] if activity == ACTIVITIES[2] else "",
                 legendas=subtitles if activity == ACTIVITIES[2] else "", observacoes=notes,
                 fonte_questoes="Idiomas", tempo_video=0, q_certas=0, q_erradas=0)
    extra.pop("tempo_segundos_exato", None)
    return dict(data=str(day), horario=str(at), grupo_muscular="Estudos", exercicio=language,
                series=0, repeticoes=0, carga_kg=0.0, descanso_seg=0, duracao_min=minutes,
                distancia_km=0.0, alimentacao_saudavel="", alimentacao_besteirol="", peso_corporal=0.0,
                dados_extras=extra)


def language_summary(records, day, language=None):
    rows, seen = [], set()
    for row in records:
        if not is_language(row) or record_date(row.get("data")) != day:
            continue
        e = extras_of(row.get("dados_extras"))
        if language and e.get("idioma") != language:
            continue
        if row.get("id") is not None:
            if row["id"] in seen:
                continue
            seen.add(row["id"])
        rows.append(row)
    return dict(minutes=sum(number(r.get("duracao_min")) for r in rows),
                review_minutes=sum(number(r.get("duracao_min")) for r in rows if extras_of(r.get("dados_extras")).get("atividade_idioma") == ACTIVITIES[0]),
                reviewed=sum(number(extras_of(r.get("dados_extras")).get("cards_revisados")) for r in rows),
                added=sum(number(extras_of(r.get("dados_extras")).get("cards_adicionados")) for r in rows),
                episodes=sum(number(extras_of(r.get("dados_extras")).get("episodios")) for r in rows), sessions=len(rows))


def language_week(records, day, language=None):
    return [dict(day=day-timedelta(days=n), **language_summary(records, day-timedelta(days=n), language)) for n in range(6, -1, -1)]
