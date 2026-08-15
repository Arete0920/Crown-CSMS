/**
 * api/aid_wizard.js
 *
 * Uses the shared canonical JSON client for auth, school scoping, and payload parsing.
 */
import { apiJson } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export async function createAidWizardSession() {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/`;
  return apiJson(url, { method: "POST", body: JSON.stringify({}) });
}

export async function configureAidWizardSession(sessionId, aidYear) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/configure/`;
  return apiJson(url, { method: "POST", body: JSON.stringify({ aid_year: aidYear }) });
}

export async function saveAidBuckets(sessionId, buckets) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/buckets/`;
  return apiJson(url, { method: "POST", body: JSON.stringify({ buckets }) });
}

export async function stageAidAwards(sessionId, awards) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/awards/`;
  return apiJson(url, { method: "POST", body: JSON.stringify({ awards }) });
}

export async function commitAidSetup(sessionId) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/commit/`;
  return apiJson(url, { method: "POST", body: JSON.stringify({ confirm: true }) });
}

export async function verifyAidSetup(sessionId) {
  const url = `${API_BASE}/api/v1/aid-wizard/sessions/${sessionId}/verify/`;
  return apiJson(url, { method: "GET" });
}
