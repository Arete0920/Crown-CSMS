function pickCorrelationId(headers) {
  if (!headers) return "";
  // Common header names we may emit from backend/proxies
  return (
    headers.get("x-correlation-id") ||
    headers.get("x-request-id") ||
    headers.get("request-id") ||
    ""
  );
}

/**
 * httpJson(url, options)
 * - returns { ok, status, data, error, correlationId }
 * - never throws for non-2xx; gives you structured error output.
 */
export async function httpJson(url, options = {}) {
  let res;
  try {
    res = await fetch(url, options);
  } catch (e) {
    return {
      ok: false,
      status: 0,
      data: null,
      correlationId: "",
      error: e?.message || "Network error",
    };
  }

  const correlationId = pickCorrelationId(res.headers);

  // Try to parse json; if not json, capture text
  const contentType = res.headers.get("content-type") || "";
  let payload = null;
  try {
    if (contentType.includes("application/json")) payload = await res.json();
    else payload = await res.text();
  } catch {
    payload = null;
  }

  if (res.ok) {
    return { ok: true, status: res.status, data: payload, correlationId, error: "" };
  }

  // Normalize error message
  const msg =
    (payload && payload.detail) ||
    (typeof payload === "string" && payload) ||
    `HTTP ${res.status}`;

  return { ok: false, status: res.status, data: payload, correlationId, error: msg };
}
