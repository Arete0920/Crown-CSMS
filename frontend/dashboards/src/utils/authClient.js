/**
 * authClient.js
 * - Stores JWT access token in localStorage.
 * - Provides authenticatedFetch which adds Authorization header if token exists.
 * - Keeps cookie/session auth working (we DO NOT disable credentials).
 */

// Canonical storage keys (single source of truth)
export const AUTH_STORAGE_KEYS = {
  accessToken: "crown.accessToken",
  refreshToken: "crown.refreshToken",
  schoolId: "crown.schoolId",
};

const TOKEN_KEY = AUTH_STORAGE_KEYS.accessToken;
const SCHOOL_KEY = AUTH_STORAGE_KEYS.schoolId;

export function getSelectedSchoolId() {
  try {
    return localStorage.getItem(SCHOOL_KEY) || "";
  } catch {
    return "";
  }
}

export function setSelectedSchoolId(schoolId) {
  try {
    const v = (schoolId || "").trim();
    if (v) localStorage.setItem(SCHOOL_KEY, v);
    else localStorage.removeItem(SCHOOL_KEY);
  } catch (err) {
    console.error(err);
  }
}

export function clearSelectedSchoolId() {
  setSelectedSchoolId("");
}

export function getAccessToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || "";
  } catch {
    return "";
  }
}

export function setAccessToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch (err) {
    console.error(err);
  }
}

export function clearAccessToken() {
  setAccessToken("");
}

// Read auth state from storage (debug + app use)
export function getStoredAuthState() {
  const access = localStorage.getItem(AUTH_STORAGE_KEYS.accessToken) || "";
  const refresh = localStorage.getItem(AUTH_STORAGE_KEYS.refreshToken) || "";
  const schoolId = localStorage.getItem(AUTH_STORAGE_KEYS.schoolId) || "";
  return {
    hasAccess: !!access,
    accessPreview: access ? access.slice(0, 16) + "…" : "",
    hasRefresh: !!refresh,
    schoolId,
  };
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
  if (schoolId && !headers.has("X-School-Id")) {
    headers.set("X-School-Id", schoolId);
  }

  // Keep cookies working for session-auth paths
  const finalInit = {
    ...init,
    headers,
    credentials: init.credentials ?? "include",
  };

  // --- DEBUG: capture what we actually send (no DevTools needed) ---
  try {
    const debugHeaders = {};
    if (headers instanceof Headers) {
      headers.forEach((v, k) => (debugHeaders[k] = v));
    } else {
      Object.assign(debugHeaders, headers);
    }
    window.__CROWN_LAST_AUTH_FETCH__ = {
      at: new Date().toISOString(),
      url,
      method: init?.method || "GET",
      hasAuthorization: !!(debugHeaders.Authorization || debugHeaders.authorization),
      schoolId: debugHeaders["X-School-Id"] || debugHeaders["x-school-id"] || "",
    };
  } catch (e) {
    // swallow debug errors
  }
  // --- END DEBUG ---

  const resp = await fetch(input, finalInit);

  // Throw structured error with status/url/body for diagnostics
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    const err = new Error(`HTTP ${resp.status} ${resp.statusText}`);
    err.status = resp.status;
    err.url = typeof input === "string" ? input : (input?.url || "");
    err.body = text.slice(0, 500);
    throw err;
  }

  return resp;
}

/**
 * JWT login helper.
 * Expects backend endpoint:
 *   POST /api/auth/token/  { username, password } -> { access, refresh }
 */
export async function jwtLogin({ username, password, apiBase = "" }) {
  const resp = await fetch(`${apiBase}/api/v1/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Login failed (${resp.status}): ${text}`);
  }

  const data = await resp.json();
  if (!data?.access) throw new Error("Login response missing access token");
  
  // Store using canonical keys
  localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, data.access);
  if (data.refresh) {
    localStorage.setItem(AUTH_STORAGE_KEYS.refreshToken, data.refresh);
  }
  
  return data;
}
