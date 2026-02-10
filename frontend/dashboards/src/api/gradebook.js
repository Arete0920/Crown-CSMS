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
