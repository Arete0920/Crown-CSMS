/**
 * authClient.js
 * - Stores JWT access token in sessionStorage (memory-ish, clears on browser close).
 * - Provides authenticatedFetch which adds Authorization header if token exists.
 * - Keeps cookie/session auth working (we DO NOT disable credentials).
 */

const TOKEN_KEY = "crown.jwt.access";

export function getAccessToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

export function setAccessToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch {}
}

export function clearAccessToken() {
  setAccessToken("");
}

export async function authenticatedFetch(input, init = {}) {
  const token = getAccessToken();
  const headers = new Headers(init.headers || {});

  // Add bearer token if available
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Keep cookies working for session-auth paths
  const finalInit = {
    ...init,
    headers,
    credentials: init.credentials ?? "include",
  };

  return fetch(input, finalInit);
}

/**
 * JWT login helper.
 * Expects backend endpoint:
 *   POST /api/auth/token/  { username, password } -> { access, refresh }
 */
export async function jwtLogin({ username, password, apiBase = "" }) {
  const resp = await fetch(`${apiBase}/api/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
    credentials: "include",
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Login failed (${resp.status}): ${text}`);
  }

  const data = await resp.json();
  if (!data?.access) throw new Error("Login response missing access token");
  setAccessToken(data.access);
  return data;
}
