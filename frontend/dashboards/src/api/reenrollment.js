/**
 * api/reenrollment.js
 *
 * Uses the shared crownApiClient and preserves the existing JSON/null/error
 * behavior for the reenrollment wizard flow.
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

/** Step 1: create a ReenrollmentSession */
export async function createReenrollmentSession() {
  return requestJson(`${API_BASE}/api/v1/reenrollment/sessions/`, {
    method: "POST",
    data: {},
  });
}

/** Step 2: configure session (set year label + enrollment fee, snapshot candidates) */
export async function configureSession(sessionId, targetYearLabel, enrollmentFee) {
  return requestJson(`${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/configure/`, {
    method: "POST",
    data: { target_year_label: targetYearLabel, enrollment_fee: enrollmentFee },
  });
}

/** Step 3: fetch list of eligible candidates */
export async function listCandidates(sessionId) {
  return requestJson(`${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/candidates/`);
}

/** Step 4: save student exclusion list */
export async function selectStudents(sessionId, excludedIds) {
  return requestJson(`${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/select/`, {
    method: "POST",
    data: { excluded_ids: excludedIds },
  });
}

/** Step 5: commit the re-enrollment (requires confirm flag) */
export async function commitReenrollment(sessionId) {
  return requestJson(`${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/commit/`, {
    method: "POST",
    data: { confirm: true },
  });
}

/** Step 6: verify results post-commit */
export async function verifyReenrollment(sessionId) {
  return requestJson(`${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/verify/`);
}
