"""Local nutrient arithmetic; no recognition service or network requests."""
import json
import math
from pathlib import Path


CATALOG_PATH = Path(__file__).parent / "supabase/functions/meal-analysis/nutrition_catalog.json"
NUTRIENTS = ("kcal", "protein_g", "carbs_g", "fat_g", "fiber_g")
ERRORS = {"invalid_items": "Confira os alimentos e porções (entre 0 e 2000 g por alimento)."}


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
