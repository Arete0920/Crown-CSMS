/**
 * api/financial_aid_wizard.js
 *
 * Follows the api/billing_wizard.js pattern exactly:
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

/** Step 1: create a FinancialAidWizardSession */
export async function createAidWizardSession() {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 1: configure session (aid_year) */
export async function configureAidWizardSession(sessionId, aidYear) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ aid_year: aidYear }),
  });
  return checkResponse(res, url);
}

/** Step 2: save active buck types */
export async function saveAidBuckets(sessionId, buckets) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/buckets/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ buckets }),
  });
  return checkResponse(res, url);
}

/** Step 3: stage awards */
export async function stageAidAwards(sessionId, awards) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/awards/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ awards }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit aid setup (requires confirm) */
export async function commitAidSetup(sessionId) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify committed setup */
export async function verifyAidSetup(sessionId) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/verify/`;
  const res = await fetch(url, {
    method: "GET",
    headers: headers(),
  });
  return checkResponse(res, url);
}
