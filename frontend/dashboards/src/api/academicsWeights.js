/**
 * Category Weights API client
 * Connects to /api/v1/academics/sections/{id}/categories/* endpoints
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

export function getSectionCategories(sectionId) {
  return _fetchJson(`${API_BASE}/api/v1/academics/sections/${sectionId}/categories/`);
}

export function putCategoryWeightsBatch(sectionId, payload) {
  return _fetchJson(`${API_BASE}/api/v1/academics/sections/${sectionId}/categories/weights/`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
