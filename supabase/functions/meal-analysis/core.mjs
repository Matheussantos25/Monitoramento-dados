// Local nutrient arithmetic retained for historical records and parity tests.
export const MAX_ITEMS = 12;
export const NUTRIENTS = ["kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"];

export class MealError extends Error {
  constructor(code, status = 400) { super(code); this.code = code; this.status = status; }
}
function number(value, min, max) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < min || value > max)
    throw new MealError("invalid_items");
  return value;
}
export function checkedItems(items, catalog) {
  if (!Array.isArray(items) || !items.length || items.length > MAX_ITEMS)
    throw new MealError("invalid_items");
  return items.map(item => {
    if (!item || typeof item.name !== "string" || !item.name.trim() || item.name.length > 80)
      throw new MealError("invalid_items");
    const foodId = typeof item.food_id === "string" && catalog.some(f => f.id === item.food_id) ? item.food_id : "";
    return { name: item.name.trim(), food_id: foodId,
      grams: Math.round(number(item.grams, 0, 2000) * 10) / 10,
      confidence: ["high", "medium", "low"].includes(item.confidence) ? item.confidence : "low" };
  });
}
export function nutrition(items, catalog) {
  const checked = checkedItems(items, catalog);
  const totals = Object.fromEntries(NUTRIENTS.map(key => [key, 0]));
  let missing = 0;
  for (const item of checked) {
    const food = catalog.find(f => f.id === item.food_id);
    if (!food || !item.grams) { missing++; continue; }
    for (const key of NUTRIENTS) totals[key] += food.per100[key] * item.grams / 100;
  }
  for (const key of NUTRIENTS) totals[key] = Math.round(totals[key] * 10) / 10;
  return { items: checked, totals, missing, complete: missing === 0,
    basis: "USDA FoodData Central / SR Legacy", catalog_version: "sr-2018-solem-1",
    estimated: true };
}
