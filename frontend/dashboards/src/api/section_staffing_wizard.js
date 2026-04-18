/**
 * api/section_staffing_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/section-staffing-wizard/sessions`;

/** Step 1: create session */
export async function createSectionStaffingSession() {
  const url = `${PREFIX}/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 2: configure (academic_year_id + term)
 * @param {string|null} academic_year_id - UUID of the academic year (optional)
 * @param {string} term - e.g. "2026-FALL"
 */
export async function configureSectionStaffingSession(sessionId, academic_year_id, term) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ academic_year_id, term }),
  });
}

/** Step 3: load sections pool
 * @param {Array} sections_pool - [{section_id, section_name, course_code, grade_level}]
 */
export async function loadSections(sessionId, sections_pool) {
  const url = `${PREFIX}/${sessionId}/load_sections/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sections_pool }),
  });
}

/** Step 4: stage assignments
 * @param {Array} assignments - [{section_id, teacher_id, role: "primary"|"aide"|"co-teacher"}]
 */
export async function stageAssignments(sessionId, assignments) {
  const url = `${PREFIX}/${sessionId}/stage_assignments/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ assignments }),
  });
}

/** Step 5: commit */
export async function commitSectionStaffingSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Step 6: verify */
export async function verifySectionStaffingSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
