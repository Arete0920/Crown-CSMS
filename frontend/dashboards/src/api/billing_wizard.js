/**
 * api/billing_wizard.js
 *
 * Uses the shared crownApiClient and preserves the existing JSON/null/error
 * behavior for the billing wizard flow.
 */
import { crownApiClient } from "./client";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function requestJson(url, { method = "GET", data } = {}) {
  const response = await crownApiClient.request({
    method,
    url,
    data,
    validateStatus: () => true,
  });

  if (response.status < 200 || response.status >= 300) {
    const err = new Error(`HTTP ${response.status}`);
    err.status = response.status;
    err.body = response.data ?? null;
    err.url = url;
    throw err;
  }
  return response.data ?? null;
}

/** Step 1: create a BillingWizardSession */
export async function createBillingWizardSession() {
  return requestJson(`${API_BASE}/api/v1/billing-wizard/sessions/`, {
    method: "POST",
    data: {},
  });
}

/** Step 1: configure session (billing mode + term) */
export async function configureWizardSession(sessionId, term, billingMode) {
  return requestJson(`${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/configure/`, {
    method: "POST",
    data: { term, billing_mode: billingMode },
  });
}

/** Step 2: save tuition plans */
export async function savePlans(sessionId, plans) {
  return requestJson(`${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/plans/`, {
    method: "POST",
    data: { plans },
  });
}

/** Step 3: save fees */
export async function saveFees(sessionId, fees) {
  return requestJson(`${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/fees/`, {
    method: "POST",
    data: { fees },
  });
}

/** Step 5: commit billing setup (requires confirm) */
export async function commitBillingSetup(sessionId) {
  return requestJson(`${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/commit/`, {
    method: "POST",
    data: { confirm: true },
  });
}

/** Step 6: verify committed setup */
export async function verifyBillingSetup(sessionId) {
  return requestJson(`${API_BASE}/api/v1/billing-wizard/sessions/${sessionId}/verify/`);
}
