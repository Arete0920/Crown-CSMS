/**
 * Curriculum read-only API client
 * Connects to /api/curriculum/* endpoints
 */

import { authenticatedFetch } from "../utils/authClient.js";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function _fetchJson(url, headers = {}) {
  const res = await authenticatedFetch(url, { headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Curriculum fetch failed (${res.status}): ${text}`);
  }
  return res.json();
}

export function fetchCurriculumPacingSummary({ schoolId }) {
  const headers = {
    "X-School-Id": schoolId,
  };
  return _fetchJson(`${API_BASE}/api/curriculum/courses/pacing-summary/`, headers);
}

