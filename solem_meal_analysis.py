"""Local nutrient arithmetic; no recognition service or network requests."""
import json
import math
from pathlib import Path


CATALOG_PATH = Path(__file__).parent / "supabase/functions/meal-analysis/nutrition_catalog.json"
NUTRIENTS = ("kcal", "protein_g", "carbs_g", "fat_g", "fiber_g")
ERRORS = {"invalid_items": "Confira os alimentos e porções (entre 0 e 2000 g por alimento)."}


def catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def food_display_name(name):
    """Presentation only: preserve custom names and never mutate saved meals."""
    return next((food.get("display_name", food["name"]) for food in catalog()
                 if food["name"] == name), name)


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
            "basis": "USDA / TACO / TBCA / rótulo Yoki (referências por alimento)" if any(i["food_id"].startswith(("tbca-", "yoki-")) for i in clean) else "USDA FoodData Central / SR Legacy + TACO NEPA/Unicamp" if any(i["food_id"].startswith("taco-") for i in clean) else "USDA FoodData Central / SR Legacy",
            "catalog_version": "solem-nutrition-v3" if any(i["food_id"].startswith(("tbca-", "yoki-")) for i in clean) else "solem-taco-2011-sr-2018-v2" if any(i["food_id"].startswith("taco-") for i in clean) else "sr-2018-solem-1"}


def cumulative_items(items, baseline, readings):
    """Readings stay in plate-addition order. Never clamp invalid differences."""
    def weight(value, maximum):
        return (not isinstance(value, bool) and isinstance(value, (int, float))
                and math.isfinite(value) and 0 <= value <= maximum)
    if not weight(baseline, 10000) or not 1 <= len(items) <= 12 or len(items) != len(readings):
        raise ValueError("Confira o peso inicial e informe uma leitura para cada alimento (até 12).")
    result, previous = [], baseline
    for index, (item, reading) in enumerate(zip(items, readings)):
        if not weight(reading, 34000) or not 0 <= reading - previous <= 2000:
            raise ValueError(f"Leitura {index + 1}: o total não pode diminuir; cada alimento deve acrescentar de 0 a 2000 g. Não zere a balança entre alimentos.")
        result.append({**item, "grams": math.floor((reading - previous) * 10 + 0.5) / 10})
        previous = reading
    return result


def meal_details(meal_type, items, weighed=False, weighing=None):
    if weighing is not None:
        items = cumulative_items(items, weighing["baseline_g"], weighing["readings_g"])
    result = nutrition(items)
    occasional = {food["id"] for food in catalog() if food.get("category") == "occasional"}
    details = {"tipo_refeicao": meal_type, "saudaveis": [item["name"] for item in result["items"] if item["food_id"] not in occasional],
               "ocasionais": [item["name"] for item in result["items"] if item["food_id"] in occasional], "nutrition": result, "input_method": "weighed" if weighed else "photo_reviewed"}
    if weighing is not None:
        details["weighing"] = dict(mode="cumulative", baseline_g=weighing["baseline_g"], readings_g=list(weighing["readings_g"]))
    # Existing diary constraint is 4096 bytes; never enlarge it unnecessarily.
    if len(json.dumps(details, ensure_ascii=False).encode("utf-8")) > 3800:
        raise ValueError("Reduza a quantidade ou o tamanho dos nomes dos alimentos.")
    return details


def day_nutrition(meals):
    totals = dict.fromkeys(NUTRIENTS, 0.0)
    counted, partial, known_items = 0, False, 0
    for row in meals:
        if row.get("details", {}).get("sem_refeicao") is True:
            continue
        result = row.get("details", {}).get("nutrition")
        if not result:
            partial = True
            continue
        try: recomputed = nutrition(result["items"])
        except (KeyError, ValueError, TypeError):
            partial = True
            continue
        counted += 1
        known_items += len(recomputed["items"]) - recomputed["missing"]
        partial |= not recomputed["complete"]
        for key in NUTRIENTS: totals[key] += recomputed["totals"][key]
    return {"totals": {key: round(value, 1) for key, value in totals.items()}, "counted": counted, "partial": partial, "known_items": known_items}


def overview_nutrition(entries, day):
    """Only the current account's loaded diary; never treat a load failure as zero."""
    if entries is None:
        return None
    meals = [row for row in entries if row.get("kind") == "meal"
             and str(row.get("day", ""))[:10] == str(day)
             and row.get("details", {}).get("sem_refeicao") is not True]
    return {**day_nutrition(meals), "meals": len(meals)}
