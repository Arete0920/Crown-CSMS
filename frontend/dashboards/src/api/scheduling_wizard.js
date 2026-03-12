/**
 * api/scheduling_wizard.js
 *
 * Follows the billing_wizard.js pattern exactly:
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

/** Step 1: create a SchedulingWizardSession */
export async function createSchedulingWizardSession() {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 1: configure session (term + school_year) */
export async function configureSchedulingSession(sessionId, term, schoolYear) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ term, school_year: schoolYear }),
  });
  return checkResponse(res, url);
}

/** Step 2: save courses */
export async function saveSchedulingCourses(sessionId, courses) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ courses }),
  });
  return checkResponse(res, url);
}

/** Step 3: stage sections */
export async function stageSchedulingSections(sessionId, sections) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ sections }),
  });
  return checkResponse(res, url);
}

/** Step 5: commit session */
export async function commitSchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify session */
export async function verifySchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`;
  const res = await fetch(url, { headers: headers() });
  return checkResponse(res, url);
}

