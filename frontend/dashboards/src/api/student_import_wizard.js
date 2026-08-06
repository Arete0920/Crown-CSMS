/**
 * api/student_import_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/student-import-wizard/sessions`;

/** Step 1: create a StudentImportWizardSession */
export async function createStudentImportSession() {
  const url = `${PREFIX}/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 2: configure session (column_map + staged_rows) */
export async function configureStudentImportSession(sessionId, column_map, staged_rows) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column_map, staged_rows }),
  });
}

/** Step 3: preview (dry-run validation) */
export async function previewStudentImportSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/preview/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 4: commit (write students to DB) */
export async function commitStudentImportSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Step 5: verify */
export async function verifyStudentImportSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
