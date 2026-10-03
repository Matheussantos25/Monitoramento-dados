"""Account defaults, not authorization. Auth creation time preserves existing users.

Training privacy is enforced by RLS on solem_activities, never by this selector.
The preserved address is only a compatibility preference, not an admin role.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULTS = json.loads((Path(__file__).parent / "account_defaults.json").read_text(encoding="utf-8"))


def generic_account(email, created_at):
    if str(email or "").strip().casefold() == DEFAULTS["preserved_email"]:
        return False
    try:
        created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        cutoff = datetime.fromisoformat(DEFAULTS["new_accounts_since"].replace("Z", "+00:00"))
        return created.astimezone(timezone.utc) >= cutoff
    except (TypeError, ValueError):
        # Missing identity must not select the shared personal defaults.
        return True


def activity_table(generic):
    return "solem_activities" if generic else "treinos"


def personal_study_topics(topics, records):
    """Include the user's own subjects/topics, without importing legacy history."""
    from solem_progress import extras_of
    result = {key: list(values) for key, values in topics.items()}
    for row in records:
        extra = extras_of(row.get("dados_extras"))
        if row.get("grupo_muscular") != "Estudos" or extra.get("fonte_questoes") == "Anki":
            continue
        subject = str(row.get("exercicio") or "").strip()
        if not subject:
            continue
        values = result.setdefault(subject, [])
        for value in str(extra.get("topico_edital") or "").split(","):
            value = value.strip()
            if value and value not in ("Geral", "🎯 Simulado / Visão Geral") and value not in values:
                values.append(value)
        if not values:
            values.append("Fundamentos")
    return result
