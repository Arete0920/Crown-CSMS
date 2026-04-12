/**
 * api/financial_aid_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

/** Step 1: create a FinancialAidWizardSession */
export async function createAidWizardSession() {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 1: configure session (aid_year) */
export async function configureAidWizardSession(sessionId, aidYear) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ aid_year: aidYear }),
  });
}

/** Step 2: save active buck types */
export async function saveAidBuckets(sessionId, buckets) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/buckets/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ buckets }),
  });
}

/** Step 3: stage awards */
export async function stageAidAwards(sessionId, awards) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/awards/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ awards }),
  });
}

/** Step 5: commit aid setup (requires confirm) */
export async function commitAidSetup(sessionId) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Step 6: verify committed setup */
export async function verifyAidSetup(sessionId) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
