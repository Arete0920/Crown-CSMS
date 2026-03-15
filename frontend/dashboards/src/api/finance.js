import { apiGet, apiGetList } from './request';
import { buildApiPath } from '../utils/apiContracts';

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
  return apiGet(`/api/v1/finance/metrics/${buildQuery(params)}`);
}

export function fetchFinanceSummary(params = {}) {
  return apiGet(`/api/v1/dashboards/finance/summary/${buildQuery(params)}`);
}

export function fetchInvoices(params = {}) {
  const path = buildApiPath('finance.invoices.list');
  return apiGet(`${path}${buildQuery(params)}`);
}

export async function getInvoices(params = {}) {
  const path = buildApiPath('finance.invoices.list');
  if (Object.keys(params).length === 0) {
    return apiGetList(path);
  }

  const data = await apiGet(`${path}${buildQuery(params)}`);
  return toRows(data);
}

