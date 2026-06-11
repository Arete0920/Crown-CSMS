/**
 * api/section_scheduler_wizard.js
 *
 * Frontend API contract adapter for the Section Scheduler wizard.
 * Keeps the shared wizard flow contract consistent across all registered wizards.
 */
import { crownApiClient } from "./client";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSION_URL = `${API_BASE}/api/v1/section-scheduler-wizard/sessions/`;

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

export async function createSectionSchedulerWizardSession() {
  return requestJson(SESSION_URL, {
    method: "POST",
    data: {},
  });
}

export async function configureSectionSchedulerWizard(sessionId, payload = {}) {
  return requestJson(`${SESSION_URL}${sessionId}/configure/`, {
    method: "POST",
    data: payload,
  });
}

export async function setSectionSchedulerWizardSections(sessionId, sections = []) {
  return requestJson(`${SESSION_URL}${sessionId}/sections/`, {
    method: "POST",
    data: { sections },
  });
}

export async function commitSectionSchedulerWizard(sessionId) {
  return requestJson(`${SESSION_URL}${sessionId}/commit/`, {
    method: "POST",
    data: { confirm: true },
  });
}

export async function verifySectionSchedulerWizard(sessionId) {
  return requestJson(`${SESSION_URL}${sessionId}/verify/`);
}
