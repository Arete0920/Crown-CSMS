/**
 * api/enrollment_period_wizard.js
 *
 * Frontend API contract adapter for the Enrollment Period wizard.
 * Keeps the shared wizard flow contract consistent across all registered wizards.
 */
import { crownApiClient } from "./client";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSION_URL = `${API_BASE}/api/v1/enrollment-period-wizard/sessions/`;

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

export async function createEnrollmentPeriodWizardSession() {
  return requestJson(SESSION_URL, {
    method: "POST",
    data: {},
  });
}

export async function configureEnrollmentPeriodWizard(sessionId, payload = {}) {
  return requestJson(`${SESSION_URL}${sessionId}/configure/`, {
    method: "POST",
    data: payload,
  });
}

export async function setEnrollmentPeriodWizardCapacities(sessionId, capacities = []) {
  return requestJson(`${SESSION_URL}${sessionId}/capacities/`, {
    method: "POST",
    data: { capacities },
  });
}

export async function commitEnrollmentPeriodWizard(sessionId) {
  return requestJson(`${SESSION_URL}${sessionId}/commit/`, {
    method: "POST",
    data: { confirm: true },
  });
}

export async function verifyEnrollmentPeriodWizard(sessionId) {
  return requestJson(`${SESSION_URL}${sessionId}/verify/`);
}
