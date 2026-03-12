/**
 * api/student_import_wizard.js
 *
 * Follows the section_assign_wizard.js pattern exactly:
 *  - getToken / getSchoolId from ../lib/api
 *  - raw fetch() with Authorization + X-School-Id headers
 *  - checkResponse with 204 guard
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/student-import-wizard/sessions`;

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

/** Step 1: create a StudentImportWizardSession */
export async function createStudentImportSession() {
  const url = `${PREFIX}/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 2: configure session (column_map + staged_rows) */
export async function configureStudentImportSession(sessionId, column_map, staged_rows) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ column_map, staged_rows }),
  });
  return checkResponse(res, url);
}

/** Step 3: preview (dry-run validation) */
export async function previewStudentImportSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/preview/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 4: commit (write students to DB) */
export async function commitStudentImportSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 5: verify */
export async function verifyStudentImportSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  const res = await fetch(url, { method: "GET", headers: headers() });
  return checkResponse(res, url);
}

