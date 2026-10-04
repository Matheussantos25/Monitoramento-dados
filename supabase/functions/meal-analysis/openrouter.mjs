import { MealError, recognitionRequest, readRecognition } from './core.mjs';

export const MEAL_MODEL = 'google/gemini-2.5-flash';
export const MONTHLY_LIMIT_USD = 1;
export const REQUEST_HEADROOM_USD = 0.02;

export function routerConfiguration(env) {
  if (!env('OPENROUTER_API_KEY')) throw new MealError('not_configured', 503);
  if (env('OPENROUTER_MEAL_MODEL') && env('OPENROUTER_MEAL_MODEL') !== MEAL_MODEL)
    throw new MealError('not_configured', 503);
  return MEAL_MODEL;
}

// The provider's native key limit is authoritative, including simultaneous requests.
// Never accept an unrestricted/shared management key or rely on a client-side counter.
export function checkedMonthlyKey(data) {
  if (!data || typeof data.limit !== 'number' || !Number.isFinite(data.limit) ||
      data.limit <= 0 || data.limit > MONTHLY_LIMIT_USD || data.limit_reset !== 'monthly' ||
      data.is_management_key !== false || data.is_provisioning_key !== false ||
      data.include_byok_in_limit !== true || typeof data.usage_monthly !== 'number' ||
      !Number.isFinite(data.usage_monthly) || data.usage_monthly < 0 ||
      typeof data.limit_remaining !== 'number' || !Number.isFinite(data.limit_remaining) ||
      data.limit_remaining > data.limit)
    throw new MealError('budget_not_configured', 503);
  if (data.usage_monthly >= data.limit || data.limit_remaining < REQUEST_HEADROOM_USD)
    throw new MealError('budget_exhausted', 429);
  return data.limit_remaining;
}

export function routerRequest(image, catalog) {
  const original = recognitionRequest(image, catalog);
  return {
    model: MEAL_MODEL, stream: false, temperature: 0.1, max_tokens: 1536,
    reasoning: { enabled: false },
    messages: [
      { role: 'system', content: original.systemInstruction.parts[0].text },
      { role: 'user', content: [
        { type: 'text', text: 'Analise somente os alimentos visíveis neste prato. Responda no esquema solicitado.' },
        { type: 'image_url', image_url: { url: `data:image/jpeg;base64,${image}` } }
      ] }
    ],
    response_format: { type: 'json_schema', json_schema: {
      name: 'solem_meal', strict: true, schema: original.generationConfig.responseJsonSchema
    } },
    provider: {
      only: ['google-vertex'], order: ['google-vertex'], allow_fallbacks: false,
      require_parameters: true, data_collection: 'deny', zdr: true,
      max_price: { prompt: 0.30, completion: 2.50 }
    }
  };
}

export async function analyzeWithOpenRouter({ image, catalog, env, reserve, fetcher = fetch }) {
  const model = routerConfiguration(env);
  const headers = { Authorization: `Bearer ${env('OPENROUTER_API_KEY')}`, 'Content-Type': 'application/json' };
  const key = await fetcher('https://openrouter.ai/api/v1/key', {
    headers, signal: AbortSignal.timeout(10000), redirect: 'error'
  });
  if (key.status === 401 || key.status === 403) throw new MealError('not_configured', 503);
  if (!key.ok) throw new MealError('provider_unavailable', 503);
  checkedMonthlyKey((await key.json()).data);
  // Reserve the existing daily/cooldown quota only after configuration and dollar budget checks.
  if (!(await reserve())) throw new MealError('quota_exhausted', 429);
  const response = await fetcher('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST', headers: { ...headers, 'HTTP-Referer': 'https://monitoramento-dados.streamlit.app',
      'X-OpenRouter-Title': 'Solem - refeicoes por foto' },
    body: JSON.stringify(routerRequest(image, catalog)), signal: AbortSignal.timeout(45000), redirect: 'error'
  });
  if (response.status === 402) throw new MealError('budget_exhausted', 429);
  if (response.status === 429) throw new MealError('quota_exhausted', 429);
  if (!response.ok) throw new MealError('provider_unavailable', 503);
  const generated = await response.json();
  if (generated.error || generated.model !== model) throw new MealError('provider_unavailable', 503);
  const choice = generated.choices?.[0];
  if (choice?.finish_reason !== 'stop' || choice.message?.refusal || typeof choice.message?.content !== 'string')
    throw new MealError('unclear_photo', 422);
  let proposed;
  try { proposed = JSON.parse(choice.message.content); } catch { throw new MealError('unclear_photo', 422); }
  return { ...readRecognition(proposed, catalog), model, provider: 'openrouter' };
}
