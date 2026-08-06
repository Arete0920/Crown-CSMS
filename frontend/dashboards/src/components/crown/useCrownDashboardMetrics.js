/**
 * useCrownDashboardMetrics
 *
 * Fetches KPI summary data for Finance and Admissions dashboards.
 * Falls back to "" for any missing field  never breaks the UI.
 *
 * Note on actual endpoint paths (as discovered from this codebase):
 *   - Financial Aid summary: /api/v1/financial-aid/summary/   this exists
 *   - Finance/billing summary: /api/v1/finance/summary/       graceful 404
 *   - Admissions summary:      /api/v1/admissions/summary/    graceful 404
 *
 * Reads auth from sessionStorage (matches authClient.js pattern):
 *   crown.jwt.access   Authorization: Bearer <token>
 *   crown.school.id    X-School-Id
 */
import { useEffect, useMemo, useState } from 'react';

function fmtMoney(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '';
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(Number(n));
  } catch {
    return '$' + String(Math.round(Number(n)));
  }
}

function fmtInt(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '';
  try {
    return new Intl.NumberFormat().format(Number(n));
  } catch {
    return String(n);
  }
}

function getSession() {
  try {
    const token = sessionStorage.getItem('crown.jwt.access') || '';
    const schoolId = sessionStorage.getItem('crown.school.id') || '';
    return { token, schoolId };
  } catch {
    return { token: '', schoolId: '' };
  }
}

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || '').trim();
  return base.endsWith('/') ? base.slice(0, -1) : base;
}

async function fetchJson(path) {
  const { token, schoolId } = getSession();
  const base = apiBase();
  const url = base ? `${base}${path}` : path;

  const headers = { Accept: 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (schoolId) headers['X-School-Id'] = schoolId;

  const res = await globalThis.fetch(url, { method: 'GET', headers });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = null;
  }
  return { ok: res.ok, status: res.status, data };
}

const INITIAL = { loaded: false, ok: false, status: 0, data: null };

/**
 * Returns:
 *   financeCards     4 KPI tiles for the Finance dashboard
 *   admissionsCards  4 KPI tiles for the Admissions dashboard
 *
 * Each tile: { label: string, value: string, hint: string }
 */
export default function useCrownDashboardMetrics() {
  const [finance, setFinance] = useState(INITIAL);
  const [admissions, setAdmissions] = useState(INITIAL);

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        const r = await fetchJson('/api/v1/finance/summary/');
        if (alive) setFinance({ loaded: true, ...r });
      } catch {
        if (alive) setFinance({ loaded: true, ok: false, status: 0, data: null });
      }
    })();

    (async () => {
      try {
        const r = await fetchJson('/api/v1/admissions/summary/');
        if (alive) setAdmissions({ loaded: true, ...r });
      } catch {
        if (alive) setAdmissions({ loaded: true, ok: false, status: 0, data: null });
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  const financeCards = useMemo(() => {
    const d = finance.data || {};
    const totalDue = d.total_due ?? d.totalDue ?? d.net_due ?? d.netDue ?? null;
    const collected = d.total_collected ?? d.collected ?? d.totalCollected ?? null;
    const openInvoices = d.open_invoices ?? d.openInvoices ?? d.invoices_open ?? null;
    const openCharges = d.open_charges ?? d.openCharges ?? d.charges_open ?? null;
    const hint = finance.loaded
      ? finance.ok
        ? 'Finance summary'
        : `Unavailable (${finance.status || 'err'})`
      : 'Loading';

    return [
      { label: 'Total Due',     value: fmtMoney(totalDue),    hint },
      { label: 'Collected',     value: fmtMoney(collected),   hint: 'Payments posted' },
      { label: 'Open Invoices', value: fmtInt(openInvoices),  hint: 'Count' },
      { label: 'Open Charges',  value: fmtInt(openCharges),   hint: 'Count' },
    ];
  }, [finance]);

  const admissionsCards = useMemo(() => {
    const d = admissions.data || {};
    const inquiries   = d.inquiries   ?? d.inquiry_count   ?? d.inquiryCount   ?? null;
    const applicants  = d.applicants  ?? d.applicant_count ?? d.applicantCount  ?? null;
    const accepted    = d.accepted    ?? d.accepted_count  ?? d.acceptedCount   ?? null;
    const enrolled    = d.enrolled    ?? d.enrolled_count  ?? d.enrolledCount   ?? null;
    const hint = admissions.loaded
      ? admissions.ok
        ? 'Admissions summary'
        : `Unavailable (${admissions.status || 'err'})`
      : 'Loading';

    return [
      { label: 'Inquiries',  value: fmtInt(inquiries),  hint },
      { label: 'Applicants', value: fmtInt(applicants), hint: 'Active pipeline' },
      { label: 'Accepted',   value: fmtInt(accepted),   hint: 'Decisions sent' },
      { label: 'Enrolled',   value: fmtInt(enrolled),   hint: 'Confirmed seats' },
    ];
  }, [admissions]);

  return { financeCards, admissionsCards };
}
