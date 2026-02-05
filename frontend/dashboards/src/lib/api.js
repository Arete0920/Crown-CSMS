import { authenticatedFetch } from "../utils/authClient";

// Keep these exports because GradebookRO expects them.
export function getToken() {
  // Delegate to whatever authClient uses, but do NOT invent a second system.
  return sessionStorage.getItem("crown.jwt.access") || "";
}

export function getSchoolId() {
  return sessionStorage.getItem("crown.school.id") || "";
}

// Canonical fetch must route through authenticatedFetch so headers/behavior match the app.
export async function apiFetch(path, opts = {}) {
  const { auth = true, ...fetchOpts } = opts;

  // authenticatedFetch already knows how to attach auth and school headers properly.
  // If you need tenant scoping toggles, that belongs INSIDE authClient, not here.
  // So apiFetch is just a pass-through.
  if (auth === false) {
    // For unauth calls, bypass authenticatedFetch ONLY if authClient provides a public client.
    // If not, add one to authClient (preferred) and call it here.
    const base = import.meta.env.VITE_API_BASE_URL || "";
    const url = path.startsWith("http") ? path : `${base}${path}`;
    const resp = await fetch(url, fetchOpts);
    if (!resp.ok) throw new Error(`HTTP ${resp.status} ${resp.statusText}`);
    const ct = resp.headers.get("content-type") || "";
    return ct.includes("application/json") ? resp.json() : resp.text();
  }

  // auth === true: single canonical path
  return authenticatedFetch(path, fetchOpts);
}
