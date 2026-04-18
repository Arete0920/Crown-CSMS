/**
 * api/grade_weights_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/grade-weights-wizard/sessions`;

/** Step 1: create session */
export async function createGradeWeightsSession() {
  const url = `${PREFIX}/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 2: configure (gradebook_id + marking_period)
 * @param {string|null} gradebook_id - UUID of the gradebook/section (optional)
 * @param {string} marking_period   - e.g. "Q1-2026"
 */
export async function configureGradeWeightsSession(sessionId, gradebook_id, marking_period) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ gradebook_id, marking_period }),
  });
}

/** Step 3: stage grade categories
 * @param {Array} categories_staged - [{name, weight_pct, drop_lowest, description}]
 *   NOTE: sum(weight_pct) must equal 100
 */
export async function stageCategories(sessionId, categories_staged) {
  const url = `${PREFIX}/${sessionId}/stage_categories/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ categories_staged }),
  });
}

/** Step 4: commit */
export async function commitGradeWeightsSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Step 5: verify */
export async function verifyGradeWeightsSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
