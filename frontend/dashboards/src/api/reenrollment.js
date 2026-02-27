/**
 * api/reenrollment.js
 *
 * Follows the api/admissions.js pattern exactly:
 *  - getToken / getSchoolId from ../lib/api
 *  - const API_BASE from VITE_API_BASE_URL
 *  - raw fetch() with manual Authorization + X-School-Id headers
 *  - explicit .json() parsing
 *  - structured error throw: { status, body, url }
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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
  // 204 No Content or empty body — return null instead of throwing a JSON parse error
  const ct = res.headers.get("content-type") || "";
  if (res.status === 204 || !ct.includes("application/json")) return null;
  return res.json();
}

/** Step 1: create a ReenrollmentSession */
export async function createReenrollmentSession() {
  const url = `${API_BASE}/api/v1/reenrollment/sessions/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 2: configure session (set year label + enrollment fee, snapshot candidates) */
export async function configureSession(sessionId, targetYearLabel, enrollmentFee) {
  const url = `${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ target_year_label: targetYearLabel, enrollment_fee: enrollmentFee }),
  });
  return checkResponse(res, url);
}

/** Step 3: fetch list of eligible candidates */
export async function listCandidates(sessionId) {
  const url = `${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/candidates/`;
  const res = await fetch(url, {
    method: "GET",
    headers: headers(),
  });
  return checkResponse(res, url);
}

/** Step 4: save student exclusion list */
export async function selectStudents(sessionId, excludedIds) {
  const url = `${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/select/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ excluded_ids: excludedIds }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit the re-enrollment (requires confirm flag) */
export async function commitReenrollment(sessionId) {
  const url = `${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify results post-commit */
export async function verifyReenrollment(sessionId) {
  const url = `${API_BASE}/api/v1/reenrollment/sessions/${sessionId}/verify/`;
  const res = await fetch(url, {
    method: "GET",
    headers: headers(),
  });
  return checkResponse(res, url);
}
