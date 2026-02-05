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
