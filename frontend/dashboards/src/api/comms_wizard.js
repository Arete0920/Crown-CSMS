/**
 * api/comms_wizard.js
 *
 * Uses the shared crownApiClient and preserves the existing JSON/null/error
 * behavior for the communications wizard flow.
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

/** Step 1: create a CommsWizardSession */
export async function createCommsWizardSession() {
  return requestJson(`${API_BASE}/api/v1/comms-wizard/sessions/`, {
    method: "POST",
    data: {},
  });
}

/** Step 1: configure session (purpose + channels) */
export async function configureCommsSession(sessionId, purpose, channels) {
  return requestJson(`${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/configure/`, {
    method: "POST",
    data: { purpose, channels },
  });
}

/** Step 2: draft message (subject + body) */
export async function draftCommsMessage(sessionId, subject, body) {
  return requestJson(`${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/message/`, {
    method: "POST",
    data: { subject, body },
  });
}

/** Step 3: stage recipients */
export async function stageCommsRecipients(sessionId, recipients) {
  return requestJson(`${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/recipients/`, {
    method: "POST",
    data: { recipients },
  });
}

/** Step 5: commit session */
export async function commitCommsSetup(sessionId) {
  return requestJson(`${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/commit/`, {
    method: "POST",
    data: { confirm: true },
  });
}

/** Step 6: verify session */
export async function verifyCommsSetup(sessionId) {
  return requestJson(`${API_BASE}/api/v1/comms-wizard/sessions/${sessionId}/verify/`);
}
