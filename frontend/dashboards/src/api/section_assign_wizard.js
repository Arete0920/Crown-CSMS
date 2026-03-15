/**
 * api/section_assign_wizard.js
 *
 * Follows the comms_wizard.js pattern exactly:
 *  - getToken / getSchoolId from ../lib/api
 *  - raw fetch() with Authorization + X-School-Id headers
 *  - checkResponse with 204 guard
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

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

/** Step 1: create a SectionAssignWizardSession */
export async function createSectionAssignSession() {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 1: configure session (section_id + optional term) */
export async function configureSectionAssignSession(sessionId, section_id, term) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ section_id, term }),
  });
  return checkResponse(res, url);
}

/** Step 2: load student pool (array of student UUID strings) */
export async function loadStudents(sessionId, student_ids) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/load/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ student_ids }),
  });
  return checkResponse(res, url);
}

/** Step 3: stage roster changes [{student_id, action: "add"|"remove"}, ...] */
export async function stageRoster(sessionId, changes) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/stage/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ changes }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit the staged roster to enrollments */
export async function commitSectionAssign(sessionId) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify final enrollment count */
export async function verifySectionAssign(sessionId) {
  const url = `${API_BASE}/api/v1/section-assign-wizard/sessions/${sessionId}/verify/`;
  const res = await fetch(url, {
    method: "GET",
    headers: headers(),
  });
  return checkResponse(res, url);
}

