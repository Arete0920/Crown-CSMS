/**
 * api/academic_year_wizard.js
 *
 * Frontend API contract adapter for the Academic Year wizard.
 * Keeps the shared wizard flow contract consistent across all registered wizards.
 */
import { crownApiClient } from "./client";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSION_URL = `${API_BASE}/api/v1/academic-year-wizard/sessions/`;

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

export async function createAcademicYearWizardSession() {
  return requestJson(SESSION_URL, {
    method: "POST",
    data: {},
  });
}

export async function configureAcademicYearWizard(sessionId, payload = {}) {
  return requestJson(`${SESSION_URL}${sessionId}/configure/`, {
    method: "POST",
    data: payload,
  });
}

export async function setAcademicYearWizardTerms(sessionId, terms = []) {
  return requestJson(`${SESSION_URL}${sessionId}/terms/`, {
    method: "POST",
    data: { terms },
  });
}

export async function commitAcademicYearWizard(sessionId) {
  return requestJson(`${SESSION_URL}${sessionId}/commit/`, {
    method: "POST",
    data: { confirm: true },
  });
}

export async function verifyAcademicYearWizard(sessionId) {
  return requestJson(`${SESSION_URL}${sessionId}/verify/`);
}
