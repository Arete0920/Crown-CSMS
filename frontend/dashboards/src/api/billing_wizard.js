/**
 * api/billing_wizard.js
 *
 * Follows the api/admissions.js / api/reenrollment.js pattern exactly:
 *  - getToken / getSchoolId from ../lib/api
 *  - raw fetch() with Authorization + X-School-Id headers
 *  - checkResponse with 204 guard
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

/** Step 1: create a BillingWizardSession */
export async function createBillingWizardSession() {
  const url = `${API_BASE}/api/v1/billing-wizard/sessions/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 1: configure session (billing mode + term) */
export async function configureWizardSession(sessionId, term, billingMode) {
  const url = `${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ term, billing_mode: billingMode }),
  });
  return checkResponse(res, url);
}

/** Step 2: save tuition plans */
export async function savePlans(sessionId, plans) {
  const url = `${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/plans/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ plans }),
  });
  return checkResponse(res, url);
}

/** Step 3: save fees */
export async function saveFees(sessionId, fees) {
  const url = `${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/fees/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ fees }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit billing setup (requires confirm) */
export async function commitBillingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify committed setup */
export async function verifyBillingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/verify/`;
  const res = await fetch(url, {
    method: "GET",
    headers: headers(),
  });
  return checkResponse(res, url);
}
