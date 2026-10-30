"""Presentation preferences and read-only insights; no new health records."""
from datetime import timedelta
from urllib.parse import urlsplit
from solem_progress import category_of, record_date, number

MEDIA_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be", "music.youtube.com", "open.spotify.com", "soundcloud.com", "www.soundcloud.com"}


def media_link(title, url):
    title, url = str(title).strip(), str(url).strip()
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme == "https" and parsed.hostname in MEDIA_HOSTS
                 and not parsed.username and not parsed.password and parsed.port in (None, 443))
    except ValueError:
        valid = False
    if not valid or not 1 <= len(title) <= 80 or len(url) > 500 or any(ord(c) < 32 for c in url):
        raise ValueError("Informe um título e um link HTTPS do YouTube, Spotify ou SoundCloud.")
    return dict(title=title, url=url)


def workout_week(records, today):
    unique = {str(r.get("id", i)): r for i, r in enumerate(records)}
    result = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        rows = [r for r in unique.values() if record_date(r.get("data")) == day and category_of(r) == "treino"]
        result.append(dict(date=day, sessions=len(rows), reps=sum(number(r.get("repeticoes")) for r in rows),
                           km=sum(number(r.get("distancia_km")) for r in rows)))
    return result
