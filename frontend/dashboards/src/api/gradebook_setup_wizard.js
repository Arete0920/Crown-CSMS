/**
 * api/gradebook_setup_wizard.js
 * Gradebook Setup Wizard â€” API layer
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSIONS = `${API_BASE}/api/v1/gradebook-setup-wizard/sessions/`;

function headers(extra = {}) {
  return {
    Authorization: `Bearer ${getToken()}`,
    "X-School-Id": getSchoolId(),
    ...extra,
  };
}

async function checkResponse(res, url) {
  if (!res.ok) {
    let body = null;
    try { body = await res.json(); } catch { /* ignore */ }
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    err.body = body;
    err.url = url;
    throw err;
  }
  const ct = res.headers.get("content-type") || "";
  if (res.status === 204 || !ct.includes("application/json")) return null;
  return res.json();
}

export async function createGradebookSetupSession() {
  const res = await fetch(SESSIONS, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, SESSIONS);
}

export async function configureGradebookSetupSession(sessionId, section_id) {
  const url = `${SESSIONS}${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ section_id }),
  });
  return checkResponse(res, url);
}

export async function defineCategories(sessionId, categories) {
  const url = `${SESSIONS}${sessionId}/categories/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ categories }),
  });
  return checkResponse(res, url);
}

export async function commitGradebookSetupSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

export async function verifyGradebookSetupSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/verify/`;
  const res = await fetch(url, { method: "GET", headers: headers() });
  return checkResponse(res, url);
}

