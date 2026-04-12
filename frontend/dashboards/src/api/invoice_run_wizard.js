/**
 * api/invoice_run_wizard.js
 * Invoice Run Wizard API layer
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSIONS = `${API_BASE}/api/v1/invoice-run-wizard/sessions/`;

export async function createInvoiceRunSession() {
  return apiFetch(SESSIONS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function configureInvoiceRunSession(sessionId, period_start, period_end, due_date) {
  const url = `${SESSIONS}${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ period_start, period_end, due_date }),
  });
}

export async function loadObligations(sessionId) {
  const url = `${SESSIONS}${sessionId}/load/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function commitInvoiceRunSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

export async function verifyInvoiceRunSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
