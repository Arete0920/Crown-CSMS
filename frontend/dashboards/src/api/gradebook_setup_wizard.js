/**
 * api/gradebook_setup_wizard.js
 * Gradebook Setup Wizard API layer
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const SESSIONS = `${API_BASE}/api/v1/gradebook-setup-wizard/sessions/`;

export async function createGradebookSetupSession() {
  return apiFetch(SESSIONS, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function configureGradebookSetupSession(sessionId, section_id) {
  const url = `${SESSIONS}${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ section_id }),
  });
}

export async function defineCategories(sessionId, categories) {
  const url = `${SESSIONS}${sessionId}/categories/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ categories }),
  });
}

export async function commitGradebookSetupSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

export async function verifyGradebookSetupSession(sessionId) {
  const url = `${SESSIONS}${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
