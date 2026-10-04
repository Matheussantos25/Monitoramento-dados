// Intentionally does not read request bodies, credentials or user data.
export function retiredResponse(request) {
  const headers = {
    "Content-Type": "application/json",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "https://monitoramento-dados.streamlit.app",
    "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });
  return new Response(JSON.stringify({
    code: "feature_removed",
    message: "O reconhecimento de refeições por API foi removido. Registre os alimentos manualmente.",
  }), { status: 410, headers });
}
