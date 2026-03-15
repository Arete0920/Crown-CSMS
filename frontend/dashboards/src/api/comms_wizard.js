/**
 * api/comms_wizard.js
 *
 * Follows the billing_wizard.js pattern exactly:
 *  - getToken / getSchoolId from ../lib/api
 *  - raw fetch() with Authorization + X-School-Id headers
 *  - checkResponse with 204 guard
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

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

/** Step 1: create a CommsWizardSession */
export async function createCommsWizardSession() {
  const url = `${API_BASE}/api/v1/comms-wizard/sessions/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 1: configure session (purpose + channels) */
export async function configureCommsSession(sessionId, purpose, channels) {
  const url = `${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ purpose, channels }),
  });
  return checkResponse(res, url);
}

/** Step 2: draft message (subject + body) */
export async function draftCommsMessage(sessionId, subject, body) {
  const url = `${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/message/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ subject, body }),
  });
  return checkResponse(res, url);
}

/** Step 3: stage recipients */
export async function stageCommsRecipients(sessionId, recipients) {
  const url = `${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/recipients/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ recipients }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit session */
export async function commitCommsSetup(sessionId) {
  const url = `${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify session */
export async function verifyCommsSetup(sessionId) {
  const url = `${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/verify/`;
  const res = await fetch(url, { headers: headers() });
  return checkResponse(res, url);
}

