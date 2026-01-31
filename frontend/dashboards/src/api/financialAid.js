/**
 * Financial Aid API client
 * Connects to backend /api/v1/financial-aid/ endpoints
 */

import { authenticatedFetch } from "../utils/authClient.js";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

/**
 * Fetch summary aggregates for financial aid
 * @param {Object} params
 * @param {string} [params.academicYear] - Optional academic year (e.g., "2025-2026")
 * @returns {Promise<Object>} Summary data with totals and awards_by_bucket
 */
export async function fetchFinancialAidSummary({ academicYear } = {}) {
  const params = new URLSearchParams();
  if (academicYear) params.set("academic_year", academicYear);

  const url = `${API_BASE}/api/v1/financial-aid/summary/?${params}`;
  const res = await authenticatedFetch(url);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch summary (${res.status}): ${text}`);
  }

  return res.json();
}

/**
 * Fetch drilldown rows for financial aid awards
 * @param {Object} params
 * @param {string} [params.academicYear] - Optional academic year
 * @param {string} [params.bucket] - Optional bucket filter (need|mission|marketing|merit|hardship)
 * @param {number} [params.limit=25] - Page size
 * @param {number} [params.offset=0] - Page offset
 * @returns {Promise<Object>} Drilldown data with count, limit, offset, rows
 */
export async function fetchFinancialAidDrilldown({ academicYear, bucket, limit = 25, offset = 0 } = {}) {
  const params = new URLSearchParams();
  if (academicYear) params.set("academic_year", academicYear);
  if (bucket) params.set("bucket", bucket);
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const url = `${API_BASE}/api/v1/financial-aid/drilldown/?${params}`;
  const res = await authenticatedFetch(url);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch drilldown (${res.status}): ${text}`);
  }

  return res.json();
}
