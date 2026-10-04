"""Photo suggestions, deterministic nutrient arithmetic, no provider credentials."""
import base64
import json
import math
from pathlib import Path

import httpx

CONSENT_VERSION = "meal-photo-openrouter-2026-10-v2"
CATALOG_PATH = Path(__file__).parent / "supabase/functions/meal-analysis/nutrition_catalog.json"
NUTRIENTS = ("kcal", "protein_g", "carbs_g", "fat_g", "fiber_g")
ERRORS = {
    "not_configured": "O reconhecimento ainda não foi ativado. Falta configurar OPENROUTER_API_KEY no backend.",
    "budget_not_configured": "Configure uma chave exclusiva no OpenRouter: limite de US$ 1, renovação mensal e Include BYOK ativado.",
    "budget_exhausted": "Orçamento mensal de reconhecimento atingido, margem insuficiente ou saldo indisponível. O registro manual continua disponível.",
    "quota_exhausted": "Limite diário ou intervalo entre análises atingido. Aguarde e tente depois; o registro manual continua disponível.",
    "session_expired": "Sua sessão expirou. Entre novamente para analisar a foto.",
    "invalid_image": "Escolha uma foto JPG, PNG ou WebP de até 8 MB, com até 20 megapixels.",
    "not_food": "Não foi possível identificar uma refeição. Envie uma foto nítida do prato.",
    "personal_content": "Use somente a foto do prato, sem rostos, documentos ou identificação pessoal.",
    "unclear_photo": "A análise não foi concluída. Tente outra foto ou registre manualmente.",
    "consent_required": "Confirme o aviso de privacidade e que você tem 18 anos ou mais.",
    "invalid_items": "Confira os alimentos e porções (entre 0 e 2000 g por alimento).",
}


def catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def nutrition(items):
    if not isinstance(items, list) or not 1 <= len(items) <= 12:
        raise ValueError(ERRORS["invalid_items"])
    table = {row["id"]: row for row in catalog()}
    clean, totals, missing = [], dict.fromkeys(NUTRIENTS, 0.0), 0
    for item in items:
        name, grams = item.get("name", ""), item.get("grams")
        if (not isinstance(name, str) or not name.strip() or len(name) > 80 or
                isinstance(grams, bool) or not isinstance(grams, (int, float)) or
                not math.isfinite(grams) or not 0 <= grams <= 2000):
            raise ValueError(ERRORS["invalid_items"])
        food_id = item.get("food_id", "")
        if food_id not in table: food_id = ""
        amount = math.floor(grams * 10 + 0.5) / 10
        confidence = item.get("confidence", "low")
        clean.append({"name": name.strip(), "food_id": food_id, "grams": amount,
                      "confidence": confidence if confidence in ("high", "medium", "low") else "low"})
        if not food_id or not amount:
            missing += 1
            continue
        for key in NUTRIENTS: totals[key] += table[food_id]["per100"][key] * amount / 100
    return {"items": clean, "totals": {key: math.floor(value * 10 + 0.5) / 10 for key, value in totals.items()},
            "missing": missing, "complete": missing == 0, "estimated": True,
            "basis": "USDA FoodData Central / SR Legacy", "catalog_version": "sr-2018-solem-1"}


def meal_details(meal_type, items):
    result = nutrition(items)
    details = {"tipo_refeicao": meal_type, "saudaveis": [item["name"] for item in result["items"]],
               "ocasionais": [], "nutrition": result, "input_method": "photo_reviewed"}
    # Existing diary constraint is 4096 bytes; never enlarge it unnecessarily.
    if len(json.dumps(details, ensure_ascii=False).encode("utf-8")) > 3800:
        raise ValueError("Reduza a quantidade ou o tamanho dos nomes dos alimentos.")
    return details


def invoke(client, body):
    try:
        session = client.auth.get_session()  # SDK refreshes an expiring token.
        if session is None: raise ValueError(ERRORS["session_expired"])
        response = httpx.post(client.supabase_url.rstrip("/") + "/functions/v1/meal-analysis",
                              headers={"Authorization": "Bearer " + session.access_token,
                                       "apikey": client.supabase_key}, json=body, timeout=90)
    except ValueError: raise
    except Exception:
        raise ValueError("Não foi possível analisar. Confira a conexão e a sessão; seu registro manual continua disponível.") from None
    try: result = response.json()
    except ValueError: result = {}
    if response.status_code == 404:
        raise ValueError(ERRORS["not_configured"])
    if not response.is_success:
        code = result.get("code")
        if response.status_code == 401: code = "session_expired"
        if response.status_code == 429 and code not in ("budget_exhausted", "quota_exhausted"):
            code = "quota_exhausted"
        raise ValueError(ERRORS.get(code, "O serviço está temporariamente indisponível. Tente depois ou registre manualmente."))
    return result


def recognize(client, jpeg, consent, adult):
    if not consent or not adult: raise ValueError(ERRORS["consent_required"])
    result = invoke(client, {"action": "recognize", "mime_type": "image/jpeg",
        "image": base64.b64encode(jpeg).decode("ascii"), "consent_version": CONSENT_VERSION, "adult": True})
    # Never trust model totals. Calculate from the checked source catalog.
    return nutrition(result.get("items"))


def day_nutrition(meals):
    totals = dict.fromkeys(NUTRIENTS, 0.0)
    counted, partial = 0, False
    for row in meals:
        result = row.get("details", {}).get("nutrition")
        if not result:
            partial = True
            continue
        try: recomputed = nutrition(result["items"])
        except (KeyError, ValueError, TypeError):
            partial = True
            continue
        counted += 1
        partial |= not recomputed["complete"]
        for key in NUTRIENTS: totals[key] += recomputed["totals"][key]
    return {"totals": {key: round(value, 1) for key, value in totals.items()}, "counted": counted, "partial": partial}
