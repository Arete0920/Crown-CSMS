/**
 * api/onboarding_wizard.js
 *
 * Student Onboarding wizard API.
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/onboarding/imports/sessions`;

/** Create a new onboarding import session. */
export async function createOnboardingSession() {
  return apiFetch(`${PREFIX}/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Configure session with student data payload. */
export async function configureOnboardingSession(sessionId, payload) {
  return apiFetch(`${PREFIX}/${sessionId}/configure/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/** Preview (dry-run validation) before commit. */
export async function previewOnboardingSession(sessionId) {
  return apiFetch(`${PREFIX}/${sessionId}/preview/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Commit the onboarding session (write to DB). */
export async function commitOnboardingSession(sessionId) {
  return apiFetch(`${PREFIX}/${sessionId}/commit/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Verify session completion status. */
export async function verifyOnboardingSession(sessionId) {
  return apiFetch(`${PREFIX}/${sessionId}/verify/`, { method: "GET" });
}
