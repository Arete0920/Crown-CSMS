/**
 * api/scheduling_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping and normalizes
 * successful responses to JSON for wizard callers.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function jsonRequest(url, options = {}) {
  const response = await apiFetch(url, options);
  return response.json();
}

export async function getSchedulingScopeOptions() {
  return jsonRequest(`${API_BASE}/api/v1/scheduling-wizard/sessions/scope-options/`, {
    method: "GET",
  });
}

export async function createSchedulingWizardSession() {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/`;
  return jsonRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

export async function configureSchedulingSession(sessionId, academicYearId, termId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`;
  return jsonRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ academic_year_id: academicYearId, term_id: termId }),
  });
}

export async function saveSchedulingCourses(sessionId, courses) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`;
  return jsonRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ courses }),
  });
}

export async function stageSchedulingSections(sessionId, sections) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`;
  return jsonRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sections }),
  });
}

export async function commitSchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`;
  return jsonRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

export async function verifySchedulingSetup(sessionId) {
  const url = `${API_BASE}/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`;
  return jsonRequest(url, { method: "GET" });
}