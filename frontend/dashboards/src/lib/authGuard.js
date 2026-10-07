/**
 * authGuard.js  session-based auth probe for CROWN.
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
 * Demo/test mode is fail-closed: browser storage may satisfy this UI guard only
 * when the build explicitly enables sandbox/certification mode. Production
 * builds always verify authentication with the backend and never treat
 * browser-controlled storage as proof of authentication.
 */

const AUTH_ME_URL = "/auth/me/";

function _demoBypassEnabled() {
  return Boolean(
    import.meta.env.VITE_DEMO_MODE === "sandbox"
    || import.meta.env.VITE_SANDBOX_MODE === "1"
    || import.meta.env.VITE_WIZARD_CERTIFICATION === "1"
  );
}

/** Read a demo-only key from browser storage. */
function _stored(key) {
  try {
    return sessionStorage.getItem(key) ?? localStorage.getItem(key) ?? null;
  } catch {
    return null;
  }
}

/** Build a synthetic session payload only for an explicitly enabled demo build. */
function _demoPayload() {
  if (!_demoBypassEnabled()) return null;
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
  // Explicit demo/certification mode only; production always probes the backend.
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
  // Explicit demo/certification mode only; production always probes the backend.
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
