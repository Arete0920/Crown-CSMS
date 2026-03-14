import { apiFetch } from "../lib/api";

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  });
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

function toRows(payload) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];
  return payload.results || payload.items || payload.rows || [];
}

export function fetchFinanceMetrics(params = {}) {
  return apiFetch(`/api/v1/finance/metrics/${buildQuery(params)}`);
}

export function fetchFinanceSummary(params = {}) {
  return apiFetch(`/api/v1/dashboards/finance/summary/${buildQuery(params)}`);
}

export function fetchInvoices(params = {}) {
  return apiFetch(`/api/billing/invoices/${buildQuery(params)}`);
}

export async function getInvoices(params = {}) {
  const data = await fetchInvoices(params);
  return toRows(data);
}

