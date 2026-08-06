/**
 * authGuard.js  session-based auth probe for Crown2026.
 *
 * Calls /auth/me/ with credentials: "include" so the browser sends the
 * session cookie that /auth/microsoft/callback/ set on login.
 *
 * Usage (inside a route loader or useEffect):
 *
 *   import { requireAuth } from '../lib/authGuard';
 *   //  ...
 *   await requireAuth(navigate);   // navigates to /login if unauthenticated
 *
 * Returns the decoded session payload on success, null on redirect.
 *
 * Demo/test mode: if sessionStorage (or localStorage) contains "crown.jwt.access"
 * the backend probe is skipped and a synthetic payload is returned from stored
 * "crown.role" / "crown.school.id" values.  This allows Playwright smoke tests
 * to seed a deterministic session without a running backend.
 */

const AUTH_ME_URL = "/auth/me/";

/** Read a key from sessionStorage, falling back to localStorage. */
function _stored(key) {
  try {
    return (
      sessionStorage.getItem(key) ?? localStorage.getItem(key) ?? null
    );
  } catch {
    return null;
  }
}

/** Build a synthetic session payload from storage (demo / Playwright mode). */
function _demoPayload() {
  const token = _stored("crown.jwt.access");
  if (!token) return null;
  return {
    email: "demo@playwright.test",
    role: _stored("crown.role") ?? "admin",
    school_id: _stored("crown.school.id") ?? null,
  };
}

/**
 * @param {function} navigate  - react-router navigate() (or any redirect fn)
 * @returns {object|null}      - session payload { email, role, school_id } or null
 */
export async function requireAuth(navigate) {
  // Demo / Playwright mode  skip backend probe entirely.
  const demo = _demoPayload();
  if (demo) return demo;

  let res;

  try {
    res = await globalThis.fetch(AUTH_ME_URL, {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
  } catch {
    // Network failure  treat as unauthenticated
    navigate("/login");
    return null;
  }

  if (!res.ok) {
    navigate("/login");
    return null;
  }

  return res.json();
}

/**
 * Lightweight authenticated-user probe  does NOT redirect.
 * Returns null when unauthenticated.
 *
 * @returns {object|null}
 */
export async function getSession() {
  // Demo / Playwright mode  skip backend probe entirely.
  const demo = _demoPayload();
  if (demo) return demo;

  try {
    const res = await globalThis.fetch(AUTH_ME_URL, {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}
