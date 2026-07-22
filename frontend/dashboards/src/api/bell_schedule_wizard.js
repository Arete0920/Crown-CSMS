/**
 * api/bell_schedule_wizard.js
 */
import { authenticatedFetch } from "../utils/authClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSIONS = `${API_BASE}/api/v1/bell-schedule-wizard/sessions/`;

function wizardFetch(url, init = {}) {
  return authenticatedFetch(url, { ...init, validateStatus: () => true });
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

export async function createBellScheduleSession() {
  const res = await wizardFetch(SESSIONS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return checkResponse(res, SESSIONS);
}

export async function configureBellScheduleSession(sessionId, label, school_year) {
  const url = `${SESSIONS}${sessionId}/configure/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, school_year }),
  });
  return checkResponse(res, url);
}

export async function definePeriods(sessionId, periods) {
  const url = `${SESSIONS}${sessionId}/periods/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ periods }),
  });
  return checkResponse(res, url);
}

export async function commitBellScheduleSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/commit/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

export async function verifyBellScheduleSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/verify/`;
  const res = await wizardFetch(url, { method: "GET" });
  return checkResponse(res, url);
}
