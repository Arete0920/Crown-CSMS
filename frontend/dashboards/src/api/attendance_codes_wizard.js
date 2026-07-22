/**
 * api/attendance_codes_wizard.js
 */
import { authenticatedFetch } from "../utils/authClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/attendance-codes-wizard/sessions`;

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

export async function createAttendanceCodesSession() {
  const url = `${PREFIX}/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

export async function configureAttendanceCodesSession(sessionId, policy_config) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ policy_config }),
  });
  return checkResponse(res, url);
}

export async function stageCodes(sessionId, codes_staged) {
  const url = `${PREFIX}/${sessionId}/stage_codes/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ codes_staged }),
  });
  return checkResponse(res, url);
}

export async function commitAttendanceCodesSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

export async function verifyAttendanceCodesSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  const res = await wizardFetch(url, { method: "GET" });
  return checkResponse(res, url);
}
