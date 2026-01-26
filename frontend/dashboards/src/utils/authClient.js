/**
 * authClient.js
 * - Stores JWT access token in sessionStorage (memory-ish, clears on browser close).
 * - Provides authenticatedFetch which adds Authorization header if token exists.
 * - Keeps cookie/session auth working (we DO NOT disable credentials).
 */

const TOKEN_KEY = "crown.jwt.access";
const SCHOOL_KEY = "crown.school.id";

export function getSelectedSchoolId() {
  try {
    return sessionStorage.getItem(SCHOOL_KEY) || "";
  } catch {
    return "";
  }
}

export function setSelectedSchoolId(schoolId) {
  try {
    const v = (schoolId || "").trim();
    if (v) sessionStorage.setItem(SCHOOL_KEY, v);
    else sessionStorage.removeItem(SCHOOL_KEY);
  } catch {}
}

export function clearSelectedSchoolId() {
  setSelectedSchoolId("");
}

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

  // Optional tenant override for staff/superusers only (backend enforces).
  const schoolId = getSelectedSchoolId();
  if (schoolId && !headers.has("X-Crown-School-Id")) {
    headers.set("X-Crown-School-Id", schoolId);
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
