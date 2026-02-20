/**
 * Gradebook read-only API client
 * Connects to /api/v1/gradebook/* endpoints
 */

import { authenticatedFetch } from "../utils/authClient.js";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function _fetchJson(url, opts = {}) {
  const res = await authenticatedFetch(url, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return res.json();
}

export function getGradebookSections({ limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  return _fetchJson(`${API_BASE}/api/v1/gradebook/sections/?${params}`);
}

export function getGradebookGrades(sectionId, opts = {}) {
  return _fetchJson(`${API_BASE}/api/v1/gradebook/sections/${sectionId}/grades/`, opts);
}

export function getSectionAssignments(sectionId, opts = {}) {
  return _fetchJson(`${API_BASE}/api/v1/gradebook/sections/${sectionId}/assignments/`, opts);
}

/**
 * Fetch drilldown rows for gradebook (paginated by student)
 * 
 * @param {string} sectionId - Section UUID
 * @param {Object} params - Query parameters
 * @param {string} params.bucket - 'all', 'missing', 'below_threshold' (default: 'all')
 * @param {number} params.threshold - Cutoff % (default: 70, used only for below_threshold)
 * @param {string} params.category_id - Optional category UUID
 * @param {number} params.limit - Default 25, max 200
 * @param {number} params.offset - Default 0
 * @returns {Promise<Object>} Drilldown data with count, limit, offset, rows
 */
export async function fetchGradebookDrilldown(sectionId, { bucket = "all", threshold = 70, limit = 25, offset = 0 } = {}) {
  const params = new URLSearchParams();
  params.set("bucket", bucket);
  params.set("threshold", String(threshold));
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const url = `${API_BASE}/api/v1/gradebook/sections/${sectionId}/drilldown/?${params}`;
  const res = await authenticatedFetch(url);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch drilldown (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * PATCH a grade entry (points_earned editing)
 * 
 * @param {string} gradeEntryId - GradeEntry UUID
 * @param {Object} payload - Fields to update
 * @param {number|null} payload.points_earned - Earned points (null for missing/blank)
 * @returns {Promise<Object>} Updated grade entry data
 */
export async function patchGradeEntry(gradeEntryId, payload) {
  const url = `${API_BASE}/api/v1/gradebook/grade-entries/${encodeURIComponent(gradeEntryId)}/`;
  const res = await authenticatedFetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PATCH grade entry failed (${res.status}): ${text}`);
  }
  return res.json();
}

/**
 * Lane 4: Bulk upsert grades for an assignment (teacher write).
 *
 * POST /api/v1/gradebook/sections/<sectionId>/assignments/<assignmentId>/grades/upsert/
 *
 * @param {string} sectionId
 * @param {string} assignmentId
 * @param {Array<{student_id: string, points_earned?: number|null}>} grades
 * @returns {Promise<{created: number, updated: number, count: number, rows: Array}>}
 */
export async function upsertAssignmentGrades(sectionId, assignmentId, grades) {
  const url = `${API_BASE}/api/v1/gradebook/sections/${encodeURIComponent(sectionId)}/assignments/${encodeURIComponent(assignmentId)}/grades/upsert/`;
  const res = await authenticatedFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ grades: grades || [] }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Upsert grades failed (${res.status}): ${text}`);
  }
  return res.json();
}
