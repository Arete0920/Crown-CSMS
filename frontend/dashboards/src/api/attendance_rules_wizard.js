/**
 * api/attendance_rules_wizard.js
 * Attendance Rules Wizard  API layer
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSIONS = `${API_BASE}/api/v1/attendance-rules-wizard/sessions/`;

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

export async function createAttendanceRulesSession() {
  const res = await globalThis.fetch(SESSIONS, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, SESSIONS);
}

export async function configureAttendanceRulesSession(sessionId, label, school_year) {
  const url = `${SESSIONS}${sessionId}/configure/`;
  const res = await globalThis.fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ label, school_year }),
  });
  return checkResponse(res, url);
}

export async function defineCodes(sessionId, codes) {
  const url = `${SESSIONS}${sessionId}/codes/`;
  const res = await globalThis.fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ codes }),
  });
  return checkResponse(res, url);
}

export async function commitAttendanceRulesSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/commit/`;
  const res = await globalThis.fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

export async function verifyAttendanceRulesSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/verify/`;
  const res = await globalThis.fetch(url, { method: "GET", headers: headers() });
  return checkResponse(res, url);
}

