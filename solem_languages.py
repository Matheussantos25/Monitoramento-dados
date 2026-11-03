"""Language sessions use the existing owner-scoped activity store, without migrating history."""
from datetime import date, time, timedelta
import calendar
import re
from solem_progress import extras_of, number, record_date

LANGUAGES = ["Inglês", "Espanhol", "Francês", "Italiano", "Alemão", "Japonês", "Coreano", "Mandarim"]
ACTIVITIES = ["Revisão no Anki", "Criação de cards", "Série / vídeo", "Leitura", "Conversação", "Escuta", "Escrita", "Aula / prática"]
SUBTITLES = ["No idioma estudado", "Em português", "Sem legenda", "Outro idioma"]
CONTENT_TYPES = ["Série", "Anime", "Filme", "Vídeo", "Podcast", "Música", "Audiolivro", "Outro"]
SOURCES = ["YouTube", "Netflix", "Prime Video", "Disney+", "Crunchyroll", "Spotify", "Arquivo / offline", "Outro"]


def media_activity(activity):
    return activity in (ACTIVITIES[2], "Escuta")


def material_label(activity):
    return {ACTIVITIES[0]: "Baralho do Anki (opcional)", ACTIVITIES[1]: "Baralho do Anki (opcional)",
            "Leitura": "Livro, artigo ou texto (opcional)", "Conversação": "Tema da conversa (opcional)",
            "Escrita": "Tema ou texto produzido (opcional)", "Aula / prática": "Curso ou assunto (opcional)"}.get(activity, "Título do conteúdo")
PERIODS = ["Dia", "Últimos 7 dias", "Mês", "Semestre", "Ano"]
SESSION_TIMES = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in range(60)]


def session_time(value):
    text = str(value or "").strip()
    if re.fullmatch(r"\d{1,2}", text):
        text = text.zfill(2) + ":00"
    elif re.fullmatch(r"\d{3,4}", text):
        text = text.zfill(4); text = text[:2] + ":" + text[2:]
    elif re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", text):
        text = text.zfill(8 if text.count(":") == 2 else 5)
    else:
        raise ValueError("Informe um horário válido: 22, 2215 ou 22:15.")
    try:
        time.fromisoformat(text)
    except ValueError:
        raise ValueError("Use um horário entre 00:00 e 23:59.") from None
    return text


def media_titles(records):
    """Only the current account's language/media history, most recent first."""
    seen, titles = set(), []
    for row in sorted(records, key=lambda r: (str(r.get("data", "")), str(r.get("horario", ""))), reverse=True):
        e = extras_of(row.get("dados_extras"))
        title = str(e.get("titulo", "")).strip()
        if is_language(row) and media_activity(e.get("atividade_idioma")) and title and title.casefold() not in seen:
            seen.add(title.casefold()); titles.append(title)
    return titles


def period_bounds(day, period):
    if period == "Dia": return day, day
    if period == "Últimos 7 dias": return day-timedelta(days=6), day
    if period == "Mês": return day.replace(day=1), day.replace(day=calendar.monthrange(day.year,day.month)[1])
    if period == "Semestre":
        first = 1 if day.month <= 6 else 7
        return date(day.year,first,1), date(day.year,first+5,calendar.monthrange(day.year,first+5)[1])
    if period == "Ano": return date(day.year,1,1), date(day.year,12,31)
    raise ValueError("Escolha um período válido.")


def language_rows(records, start, end, language=None):
    rows, seen = [], set()
    for row in records:
        day = record_date(row.get("data"))
        if not is_language(row) or day is None or not start <= day <= end:
            continue
        if language and extras_of(row.get("dados_extras")).get("idioma") != language:
            continue
        if row.get("id") is not None:
            if row["id"] in seen: continue
            seen.add(row["id"])
        rows.append(row)
    return rows


def language_period_summary(records, start, end, language=None):
    rows = language_rows(records,start,end,language)
    return dict(minutes=sum(number(r.get("duracao_min")) for r in rows),
                review_minutes=sum(number(r.get("duracao_min")) for r in rows if extras_of(r.get("dados_extras")).get("atividade_idioma") == ACTIVITIES[0]),
                reviewed=sum(number(extras_of(r.get("dados_extras")).get("cards_revisados")) for r in rows),
                added=sum(number(extras_of(r.get("dados_extras")).get("cards_adicionados")) for r in rows),
                episodes=sum(number(extras_of(r.get("dados_extras")).get("episodios")) for r in rows), sessions=len(rows),
                active_days=len({record_date(r.get("data")) for r in rows}))


def language_chart(records, start, end, period, language=None):
    rows = language_rows(records,start,end,language)
    if period == "Dia":
        keys = [f"{h:02d}h" for h in range(24)]
        bucket = lambda r: str(r.get("horario", "00:00"))[:2].zfill(2)+"h"
    elif period in ("Semestre", "Ano"):
        keys = [f"{m:02d}/{start.year}" for m in range(start.month,end.month+1)]
        bucket = lambda r: record_date(r["data"]).strftime("%m/%Y")
    else:
        keys = [(start+timedelta(days=n)).strftime("%d/%m") for n in range((end-start).days+1)]
        bucket = lambda r: record_date(r["data"]).strftime("%d/%m")
    totals = dict.fromkeys(keys,0)
    for row in rows:
        key = bucket(row)
        if key in totals: totals[key] += number(row.get("duracao_min"))
    return [dict(label=k,minutes=n) for k,n in totals.items()]


def is_language(row):
    return row.get("grupo_muscular") == "Estudos" and extras_of(row.get("dados_extras")).get("language_schema") == 1


def language_session(day, at, language, activity, minutes, *, title="", reviewed=0, added=0,
                     episodes=0, audio="", subtitles="", notes="", previous=None, source="", content_type=""):
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
    media = media_activity(activity)
    if len(source.strip()) > 100 or (content_type and content_type not in CONTENT_TYPES):
        raise ValueError("Confira a fonte e o tipo de conteúdo.")
    if media and (episodes > 100 or (subtitles and subtitles not in SUBTITLES)):
        raise ValueError("Confira a quantidade de conteúdos e as legendas.")
    # Only fields belonging to the current activity survive a change of type.
    extra = dict(extras_of((previous or {}).get("dados_extras")))
    extra.update(language_schema=1, idioma=language, atividade_idioma=activity, titulo=title,
                 cards_revisados=reviewed if activity == ACTIVITIES[0] else 0,
                 cards_adicionados=added if activity in ACTIVITIES[:2] else 0,
                 episodios=episodes if media else 0,
                 idioma_audio=audio.strip()[:60] if media else "",
                 legendas=subtitles if media else "", observacoes=notes,
                 fonte_idioma=source.strip() if activity not in ACTIVITIES[:2] else "",
                 tipo_conteudo=content_type if media else "",
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
