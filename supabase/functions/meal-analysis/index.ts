import catalog from "./nutrition_catalog.json" with { type: "json" };
import { MealError, checkedPhoto, nutrition, readRecognition, recognitionRequest, freeConfiguration } from "./core.mjs";

const env = (name: string) => Deno.env.get(name) || "";
const allowed = new Set(["https://monitoramento-dados.streamlit.app", "http://localhost:8501", "http://127.0.0.1:8501"]);
const MAX_REQUEST = 6 * 1024 * 1024;
async function bodyOf(req: Request) {
  if (!req.body || Number(req.headers.get("content-length") || 0) > MAX_REQUEST) throw new MealError("invalid_image");
  const reader = req.body.getReader(); const parts: Uint8Array[] = []; let length = 0;
  try {
    while (true) {
      const { done, value } = await reader.read(); if (done) break;
      length += value.length;
      if (length > MAX_REQUEST) { await reader.cancel(); throw new MealError("invalid_image"); }
      parts.push(value);
    }
  } finally { reader.releaseLock(); }
  const all = new Uint8Array(length); let offset = 0;
  for (const part of parts) { all.set(part, offset); offset += part.length; }
  try { return JSON.parse(new TextDecoder().decode(all)); } catch { throw new MealError("invalid_request"); }
}
// No service-role key, image storage, request logging or paid-provider fallback.
Deno.serve(async req => {
  const origin = req.headers.get("origin");
  const headers = { "Content-Type": "application/json", "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": origin && allowed.has(origin) ? origin : "https://monitoramento-dados.streamlit.app",
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info", "Access-Control-Allow-Methods": "POST, OPTIONS", "Vary": "Origin" };
  const reply = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status, headers });
  if (origin && !allowed.has(origin)) return reply({ code: "forbidden_origin" }, 403);
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers });
  if (req.method !== "POST") return reply({ code: "method_not_allowed" }, 405);
  try {
    const auth = req.headers.get("authorization") || "";
    if (!/^Bearer \S+$/.test(auth)) throw new MealError("session_expired", 401);
    const sbHeaders = { apikey: env("SUPABASE_ANON_KEY"), Authorization: auth, "Content-Type": "application/json" };
    const user = await fetch(`${env("SUPABASE_URL")}/auth/v1/user`, { headers: sbHeaders, signal: AbortSignal.timeout(10000) });
    if (!user.ok || !(await user.json()).id) throw new MealError("session_expired", 401);
    const body = await bodyOf(req);
    if (!body || typeof body !== "object") throw new MealError("invalid_request");
    if (body.action === "catalog") return reply({ catalog });
    if (body.action === "calculate") return reply(nutrition(body.items, catalog));
    if (body.action !== "recognize") throw new MealError("invalid_request");
    const image = checkedPhoto(body); const model = freeConfiguration(env);
    // Atomically enforce shared daily, per-user daily and short cooldown quotas in PostgreSQL.
    const budget = await fetch(`${env("SUPABASE_URL")}/rest/v1/rpc/solem_reserve_meal_analysis`, {
      method: "POST", headers: sbHeaders, body: "{}", signal: AbortSignal.timeout(10000) });
    if (!budget.ok) throw new MealError("backend_unavailable", 503);
    if ((await budget.json()) !== true) throw new MealError("quota_exhausted", 429);
    const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
      method: "POST", headers: { "Content-Type": "application/json", "x-goog-api-key": env("GEMINI_API_KEY") },
      body: JSON.stringify(recognitionRequest(image, catalog)), signal: AbortSignal.timeout(45000) });
    if (response.status === 429) throw new MealError("quota_exhausted", 429);
    if (!response.ok) throw new MealError("provider_unavailable", 503);
    const generated = await response.json();
    const candidate = generated.candidates?.[0];
    if (candidate?.finishReason !== "STOP") throw new MealError("unclear_photo", 422);
    const output = candidate.content?.parts?.filter((part: { thought?: boolean }) => !part.thought)
      .map((part: { text?: string }) => part.text || "").join("");
    let proposed;
    try { proposed = JSON.parse(output || ""); } catch { throw new MealError("unclear_photo", 422); }
    return reply({ ...readRecognition(proposed, catalog), model });
  } catch (error) {
    // Never return/log upstream responses, keys, JWTs, photos or personal data.
    const known = error instanceof MealError;
    return reply({ code: known ? error.code : "backend_unavailable" }, known ? error.status : 503);
  }
});
