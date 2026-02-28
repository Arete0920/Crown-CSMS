/**
 * api/grade_weights_wizard.js
 *
 * Follows the section_assign_wizard.js pattern exactly.
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const PREFIX = `${API_BASE}/api/v1/grade-weights-wizard/sessions`;

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
export async function createGradeWeightsSession() {
  const url = `${PREFIX}/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 2: configure (gradebook_id + marking_period)
 * @param {string|null} gradebook_id - UUID of the gradebook/section (optional)
 * @param {string} marking_period   - e.g. "Q1-2026"
 */
export async function configureGradeWeightsSession(sessionId, gradebook_id, marking_period) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ gradebook_id, marking_period }),
  });
  return checkResponse(res, url);
}

/** Step 3: stage grade categories
 * @param {Array} categories_staged - [{name, weight_pct, drop_lowest, description}]
 *   NOTE: sum(weight_pct) must equal 100
 */
export async function stageCategories(sessionId, categories_staged) {
  const url = `${PREFIX}/${sessionId}/stage_categories/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ categories_staged }),
  });
  return checkResponse(res, url);
}

/** Step 4: commit */
export async function commitGradeWeightsSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 5: verify */
export async function verifyGradeWeightsSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  const res = await fetch(url, { method: "GET", headers: headers() });
  return checkResponse(res, url);
}
