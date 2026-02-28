/**
 * api/section_staffing_wizard.js
 *
 * Follows the section_assign_wizard.js pattern exactly.
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const PREFIX = `${API_BASE}/api/v1/section-staffing-wizard/sessions`;

function headers(extra = {}) {
  return {
    Authorization: `Bearer ${getToken()}`,
    "X-School-Id": getSchoolId(),
    ...extra,
  };
}

async function checkResponse(res, url) {
  if (!res.ok) {
    let body = null;
    try { body = await res.json(); } catch { /* ignore */ }
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    err.body = body;
    err.url = url;
    throw err;
  }
  const ct = res.headers.get("content-type") || "";
  if (res.status === 204 || !ct.includes("application/json")) return null;
  return res.json();
}

/** Step 1: create session */
export async function createSectionStaffingSession() {
  const url = `${PREFIX}/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 2: configure (academic_year_id + term)
 * @param {string|null} academic_year_id - UUID of the academic year (optional)
 * @param {string} term - e.g. "2026-FALL"
 */
export async function configureSectionStaffingSession(sessionId, academic_year_id, term) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ academic_year_id, term }),
  });
  return checkResponse(res, url);
}

/** Step 3: load sections pool
 * @param {Array} sections_pool - [{section_id, section_name, course_code, grade_level}]
 */
export async function loadSections(sessionId, sections_pool) {
  const url = `${PREFIX}/${sessionId}/load_sections/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ sections_pool }),
  });
  return checkResponse(res, url);
}

/** Step 4: stage assignments
 * @param {Array} assignments - [{section_id, teacher_id, role: "primary"|"aide"|"co-teacher"}]
 */
export async function stageAssignments(sessionId, assignments) {
  const url = `${PREFIX}/${sessionId}/stage_assignments/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ assignments }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit */
export async function commitSectionStaffingSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify */
export async function verifySectionStaffingSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  const res = await fetch(url, { method: "GET", headers: headers() });
  return checkResponse(res, url);
}
