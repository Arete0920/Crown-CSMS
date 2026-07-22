/**
 * api/enrollment_conversion_wizard.js
 */
import { authenticatedFetch } from "../utils/authClient";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSIONS = `${API_BASE}/api/v1/enrollment-conversion-wizard/sessions/`;

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

export async function createEnrollmentConversionSession() {
  const res = await wizardFetch(SESSIONS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return checkResponse(res, SESSIONS);
}

export async function configureEnrollmentConversionSession(sessionId, academic_year_label, from_status) {
  const url = `${SESSIONS}${sessionId}/configure/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ academic_year_label, from_status }),
  });
  return checkResponse(res, url);
}

export async function loadApplicants(sessionId) {
  const url = `${SESSIONS}${sessionId}/load/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

export async function commitEnrollmentConversionSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/commit/`;
  const res = await wizardFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

export async function verifyEnrollmentConversionSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/verify/`;
  const res = await wizardFetch(url, { method: "GET" });
  return checkResponse(res, url);
}
