/**
 * api/section_assign_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

/** Step 1: create a SectionAssignWizardSession */
export async function createSectionAssignSession() {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 1: configure session (section_id + optional term) */
export async function configureSectionAssignSession(sessionId, section_id, term) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ section_id, term }),
  });
}

/** Step 2: load student pool (array of student UUID strings) */
export async function loadStudents(sessionId, student_ids) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/load/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ student_ids }),
  });
}

/** Step 3: stage roster changes [{student_id, action: "add"|"remove"}, ...] */
export async function stageRoster(sessionId, changes) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/stage/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ changes }),
  });
}

/** Step 5: commit the staged roster to enrollments */
export async function commitSectionAssign(sessionId) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Step 6: verify final enrollment count */
export async function verifySectionAssign(sessionId) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
