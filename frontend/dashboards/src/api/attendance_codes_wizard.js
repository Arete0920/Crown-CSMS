/**
 * api/attendance_codes_wizard.js
 *
 * Follows the section_assign_wizard.js pattern exactly.
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const PREFIX = `${API_BASE}/api/v1/attendance-codes-wizard/sessions`;

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
export async function createAttendanceCodesSession() {
  const url = `${PREFIX}/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 2: configure policy
 * @param {object} policy_config - {school_year, applies_to_grades: []}
 */
export async function configureAttendanceCodesSession(sessionId, policy_config) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ policy_config }),
  });
  return checkResponse(res, url);
}

/** Step 3: stage codes
 * @param {Array} codes_staged - [{code, label, excused, counts_as_tardy, counts_as_absent, notify_guardian}]
 */
export async function stageCodes(sessionId, codes_staged) {
  const url = `${PREFIX}/${sessionId}/stage_codes/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ codes_staged }),
  });
  return checkResponse(res, url);
}

/** Step 4: commit */
export async function commitAttendanceCodesSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 5: verify */
export async function verifyAttendanceCodesSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  const res = await fetch(url, { method: "GET", headers: headers() });
  return checkResponse(res, url);
}
