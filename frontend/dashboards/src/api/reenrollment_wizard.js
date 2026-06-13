/**
 * api/reenrollment_wizard.js
 *
 * Re-enrollment wizard API.
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/reenrollment/sessions`;

/** Create a new re-enrollment session. */
export async function createReenrollmentSession() {
  return apiFetch(`${PREFIX}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Add or update students in the session. */
export async function configureReenrollmentSession(sessionId, studentIds) {
  return apiFetch(`${PREFIX}/${sessionId}/configure/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_ids: studentIds }),
  });
}

/** Preview eligibility and errors before confirming. */
export async function previewReenrollmentSession(sessionId) {
  return apiFetch(`${PREFIX}/${sessionId}/preview/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Confirm and commit re-enrollment for all approved students. */
export async function commitReenrollmentSession(sessionId) {
  return apiFetch(`${PREFIX}/${sessionId}/commit/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Verify session completion status. */
export async function verifyReenrollmentSession(sessionId) {
  return apiFetch(`${PREFIX}/${sessionId}/verify/`, { method: "GET" });
}
