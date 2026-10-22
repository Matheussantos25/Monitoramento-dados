"""Versioned private documents stored as notes; no schema or permission changes."""
import json

PREFIX = "SOLEM_SCRIPT_V1\n"

def script_data(item):
    if item.get("kind") != "note" or not item.get("body", "").startswith(PREFIX):
        return None
    try:
        data = json.loads(item["body"][len(PREFIX):])
        if (data.get("type") not in ("idea", "script") or
                any(not isinstance(data.get(k), str) for k in ("text", "description", "tags"))):
            return None
        return data
    except (ValueError, TypeError, AttributeError):
        return None

def script_body(kind, text, description, tags):
    if kind not in ("idea", "script") or len(text)>40000 or len(description)>3000 or len(tags)>500:
        raise ValueError("Use até 40 mil caracteres no texto, 3 mil na descrição e 500 nas tags.")
    body = PREFIX + json.dumps(dict(type=kind,text=text,description=description,tags=tags),ensure_ascii=False)
    if len(body)>50000:
        raise ValueError("Conteúdo muito longo para salvar. Reduza o texto.")
    return body
