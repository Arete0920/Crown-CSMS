/**
 * api/invoice_run_wizard.js
 * Invoice Run Wizard API layer
 */
import { apiJson } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSIONS = `${API_BASE}/api/v1/invoice-run-wizard/sessions/`;

export async function createInvoiceRunSession() {
  return apiJson(SESSIONS, { method: "POST", body: JSON.stringify({}) });
}

export async function configureInvoiceRunSession(sessionId, period_start, period_end, due_date) {
  return apiJson(`${SESSIONS}${sessionId}/configure/`, {
    method: "POST",
    body: JSON.stringify({ period_start, period_end, due_date }),
  });
}

export async function loadObligations(sessionId) {
  return apiJson(`${SESSIONS}${sessionId}/load/`, { method: "POST", body: JSON.stringify({}) });
}

export async function commitInvoiceRunSession(sessionId) {
  return apiJson(`${SESSIONS}${sessionId}/commit/`, {
    method: "POST",
    body: JSON.stringify({ confirm: true }),
  });
}

export async function verifyInvoiceRunSession(sessionId) {
  return apiJson(`${SESSIONS}${sessionId}/verify/`, { method: "GET" });
}
