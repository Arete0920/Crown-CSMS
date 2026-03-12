/**
 * api/guardian_household_wizard.js
 *
 * Follows the section_assign_wizard.js pattern exactly.
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/guardian-household-wizard/sessions`;

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
export async function createGuardianHouseholdSession() {
  const url = `${PREFIX}/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 2: configure household
 * @param {object} household_data - {name, address: {street, city, state, zip}}
 */
export async function configureGuardianHouseholdSession(sessionId, household_data) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ household_data }),
  });
  return checkResponse(res, url);
}

/** Step 3: add guardians
 * @param {Array} guardian_data - [{name, email, custody_type, contact_priority, receives_communications}]
 */
export async function addGuardians(sessionId, guardian_data) {
  const url = `${PREFIX}/${sessionId}/add_guardians/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ guardian_data }),
  });
  return checkResponse(res, url);
}

/** Step 4: link students
 * @param {Array} link_data - [{student_id, relationship}]
 */
export async function linkStudents(sessionId, link_data) {
  const url = `${PREFIX}/${sessionId}/link_students/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ link_data }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit */
export async function commitGuardianHouseholdSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify */
export async function verifyGuardianHouseholdSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  const res = await fetch(url, { method: "GET", headers: headers() });
  return checkResponse(res, url);
}

