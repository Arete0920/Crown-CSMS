/**
 * api/scheduling_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

/** Step 1: create a SchedulingWizardSession */
export async function createSchedulingWizardSession() {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 1: configure session (term + school_year) */
export async function configureSchedulingSession(sessionId, term, schoolYear) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ term, school_year: schoolYear }),
  });
}

/** Step 2: save courses */
export async function saveSchedulingCourses(sessionId, courses) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ courses }),
  });
}

/** Step 3: stage sections */
export async function stageSchedulingSections(sessionId, sections) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sections }),
  });
}

/** Step 5: commit session */
export async function commitSchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Step 6: verify session */
export async function verifySchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
