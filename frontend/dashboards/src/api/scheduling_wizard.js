/**
 * api/scheduling_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export async function getSchedulingScopeOptions() {
  return apiFetch(`${API_BASE}/api/v1/scheduling-wizard/sessions/scope-options/`, {
    method: "GET",
  });
}

export async function createSchedulingWizardSession() {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function configureSchedulingSession(sessionId, academicYearId, termId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ academic_year_id: academicYearId, term_id: termId }),
  });
}

export async function saveSchedulingCourses(sessionId, courses) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ courses }),
  });
}

export async function stageSchedulingSections(sessionId, sections) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sections }),
  });
}

export async function commitSchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

export async function verifySchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}