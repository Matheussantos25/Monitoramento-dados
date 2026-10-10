"""Private mission preferences and creator progress. Never rewrites legacy XP."""
from copy import deepcopy
from datetime import date
from math import isfinite
from uuid import UUID, uuid4
from solem_progress import record_date
from solem_workspace import mind_nodes

GOALS = {
    "water": ("Água", "ml", 3000, 10000),
    "mewing": ("Mewing com borracha", "rep", 400, 10000),
    "flexao": ("Flexões", "rep", 50, 10000),
    "agachamento": ("Agachamentos", "rep", 50, 10000),
    "cardio": ("Caminhada ou corrida", "km", 5, 100),
    "questions": ("Questões", "questões", 150, 10000),
    "study": ("Tempo de estudo", "min", 60, 1440),
    "created": ("Vídeos criados", "vídeos", 2, 100),
    "published": ("Vídeos publicados", "vídeos", 2, 100),
}
STAGES = ("Ideia", "Roteiro", "Gravação", "Edição", "Pronto", "Publicado")
ACCENTS = {"Ciano": "#83DCFF", "Violeta": "#B8A5FF", "Âmbar": "#F4C87D"}
CREATOR_RANKS = ("Iniciante", "Aprendiz", "Criador", "Especialista", "Veterano", "Mestre")
CREATOR_LIMITS = (0, 100, 300, 750, 1500, 3000)


def defaults(personal=False, generic=False):
    targets = {key: values[2] for key, values in GOALS.items()}
    enabled = list(GOALS)
    if generic:
        from solem_account import DEFAULTS
        targets.update(DEFAULTS["checkup_targets"])
        enabled.remove("mewing")
    if personal:
        targets.update(flexao=100, agachamento=100)
        enabled = [key for key in enabled if key not in ("questions", "study")]
    else:
        enabled = [key for key in enabled if key not in ("created", "published")]
    root = "Canal principal · Gacha" if personal else "Meus canais"
    return dict(targets=targets, enabled=enabled, accent="Ciano", effects=True,
                sound=True, strategy=f"{root}\n  Ideias\n  Roteiro\n  Gravação\n  Edição\n  Publicação")


def preferences(saved=None, personal=False, generic=False):
    result = defaults(personal, generic)
    if saved:
        result.update({k: v for k, v in saved.items() if k in result and k != "targets"})
        result["targets"].update(saved.get("targets", {}))
    if set(result["targets"]) != set(GOALS):
        raise ValueError("Meta desconhecida.")
    for key, value in result["targets"].items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
            raise ValueError("As metas devem ser números válidos.")
        if not 0 < value <= GOALS[key][3] or (key != "cardio" and value != int(value)):
            raise ValueError(f"Revise a meta de {GOALS[key][0]}.")
    enabled = result["enabled"]
    if not isinstance(enabled, list) or any(k not in GOALS for k in enabled):
        raise ValueError("Seleção de metas inválida.")
    result["enabled"] = list(dict.fromkeys(enabled))
    if generic:
        result["enabled"] = [k for k in result["enabled"] if k != "mewing"]
    if result["accent"] not in ACCENTS or any(type(result[k]) is not bool for k in ("effects", "sound")):
        raise ValueError("Preferências de aparência inválidas.")
    if len(result["strategy"]) > 10000:
        raise ValueError("O mapa deve ter até 10.000 caracteres.")
    mind_nodes(result["strategy"])
    return result


def validate_creator(data):
    result = {k: data.get(k) for k in ("kind", "title", "body", "channel_id", "stage", "produced_on", "published_on", "url")}
    result["title"] = str(result["title"] or "").strip()
    result["body"] = str(result["body"] or "").strip()
    result["url"] = str(result["url"] or "").strip()
    if result["kind"] not in ("channel", "video") or not 1 <= len(result["title"]) <= 160:
        raise ValueError("Informe um título de até 160 caracteres.")
    if len(result["body"]) > 10000 or len(result["url"]) > 2000:
        raise ValueError("Descrição ou link muito longo.")
    if result["url"] and not result["url"].startswith(("https://", "http://")):
        raise ValueError("Use um link iniciado por https:// ou http://.")
    if result["kind"] == "channel":
        result.update(channel_id=None, stage=None, produced_on=None, published_on=None)
        return result
    try:
        UUID(str(result["channel_id"]))
    except (ValueError, TypeError):
        raise ValueError("Escolha o canal deste vídeo.") from None
    if result["stage"] not in STAGES:
        raise ValueError("Etapa inválida.")
    for key in ("produced_on", "published_on"):
        if result[key] is not None:
            try:
                result[key] = date.fromisoformat(str(result[key])).isoformat()
            except (TypeError, ValueError):
                raise ValueError("Data inválida.") from None
    if result["stage"] in ("Pronto", "Publicado") and not result["produced_on"]:
        raise ValueError("Informe quando o vídeo ficou pronto.")
    if (result["stage"] == "Publicado") != bool(result["published_on"]):
        raise ValueError("A data de publicação deve corresponder à etapa Publicado.")
    if result["published_on"] and result["published_on"] < result["produced_on"]:
        raise ValueError("A publicação não pode ser anterior à criação.")
    if result["stage"] not in ("Pronto", "Publicado") and result["produced_on"]:
        raise ValueError("Vídeos ainda em produção não contam como criados.")
    return result


def creator_progress(items, today):
    videos = {row["id"]: row for row in items if row.get("kind") == "video" and not row.get("archived")}
    created = published = xp = 0
    week_created = week_published = 0
    for row in videos.values():
        production, publication = record_date(row.get("produced_on")), record_date(row.get("published_on"))
        if row.get("stage") in ("Pronto", "Publicado") and production and production <= today:
            xp += 20
            created += production == today
            week_created += 0 <= (today - production).days < 7
            if row.get("stage") == "Publicado" and publication and production <= publication <= today:
                xp += 30
                published += publication == today
                week_published += 0 <= (today - publication).days < 7
    tier = max(i for i, limit in enumerate(CREATOR_LIMITS) if xp >= limit)
    return dict(created=created, published=published, week_created=week_created,
                week_published=week_published, xp=xp, tier=tier, rank=CREATOR_RANKS[tier],
                pipeline=sum(r.get("stage") not in ("Pronto", "Publicado") for r in videos.values()))


class JourneyStore:
    """Owner-scoped RLS repository. No service-role, hard delete or global cache."""
    def __init__(self, client=None, demo_state=None, demo_owner="personal"):
        self.client, self.demo_state = client, demo_state
        self.key = f"journey_demo_{demo_owner}"
        if demo_state is not None and self.key not in demo_state:
            demo_state[self.key] = dict(settings=None, items=[])

    def load(self):
        if self.demo_state is not None:
            return deepcopy(self.demo_state[self.key])
        settings = self.client.table("solem_journey_settings").select("*").execute().data
        items, offset = [], 0
        while True:
            batch = self.client.table("solem_creator_items").select("*").order("created_at").order("id").range(offset, offset + 499).execute().data
            items.extend(batch)
            if len(batch) < 500:
                break
            offset += 500
        return dict(settings=settings[0] if settings else None, items=items)

    def save_settings(self, values, old=None):
        if self.demo_state is not None:
            current = self.demo_state[self.key]["settings"]
            if (current or {}).get("revision") != (old or {}).get("revision"):
                raise ValueError("Suas metas mudaram em outra sessão. Atualize antes de salvar.")
            self.demo_state[self.key]["settings"] = dict(preferences=deepcopy(values), revision=(old or {}).get("revision", 0) + 1)
            return
        query = self.client.table("solem_journey_settings")
        result = (query.update(dict(preferences=values)).eq("owner_id", old["owner_id"]).eq("revision", old["revision"]).execute()
                  if old else query.insert(dict(preferences=values)).execute())
        if not result.data:
            raise ValueError("Suas metas mudaram em outra sessão. Atualize antes de salvar.")

    def save_item(self, values, old=None):
        clean = validate_creator(values)
        if self.demo_state is not None:
            state = self.demo_state[self.key]
            if clean["kind"] == "video" and not any(r["id"] == clean["channel_id"] and r["kind"] == "channel" and not r.get("archived") for r in state["items"]):
                raise ValueError("Escolha um canal ativo.")
            current = next((r for r in state["items"] if old and r["id"] == old["id"]), None)
            if old and (not current or current["revision"] != old["revision"]):
                raise ValueError("Registro alterado. Atualize a página.")
            row = dict(clean, id=old["id"] if old else str(uuid4()), archived=False, revision=(old or {}).get("revision", 0) + 1)
            if current:
                state["items"][state["items"].index(current)] = row
            else:
                state["items"].append(row)
            return row
        query = self.client.table("solem_creator_items")
        result = (query.update(clean).eq("id", old["id"]).eq("revision", old["revision"]).execute()
                  if old else query.insert(clean).execute())
        if not result.data:
            raise ValueError("Registro alterado. Atualize a página.")
        return result.data[0]

    def archive(self, row, value=True):
        if self.demo_state is not None:
            current = next(r for r in self.demo_state[self.key]["items"] if r["id"] == row["id"])
            if current["revision"] != row["revision"]:
                raise ValueError("Registro alterado. Atualize a página.")
            current.update(archived=value, revision=current["revision"] + 1)
            return
        result = self.client.table("solem_creator_items").update(dict(archived=value)).eq("id", row["id"]).eq("revision", row["revision"]).execute()
        if not result.data:
            raise ValueError("Registro alterado. Atualize a página.")
