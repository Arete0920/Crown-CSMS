import { apiFetch } from "../lib/api";

const BASE = "/api/v1/home-academy";

async function requestJson(path, { method = "GET", body } = {}) {
  const response = await apiFetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload.detail || payload.error || "Home Academy request failed.");
    error.status = response.status;
    error.code = payload.code;
    error.payload = payload;
    throw error;
  }
  return payload;
}

export function fetchHomeAcademyConfig() {
  return requestJson("/config/");
}

export function fetchHomeAcademyOfferings() {
  return requestJson("/offerings/");
}

export function fetchHomeAcademyEnrollments() {
  return requestJson("/enrollments/");
}

export function fetchHomeAcademyRegistrations() {
  return requestJson("/offering-enrollments/");
}

export function fetchHomeAcademyAidRules() {
  return requestJson("/financial-aid-rules/");
}

export function fetchHomeAcademyBoardSummary() {
  return requestJson("/board/summary/");
}

export function fetchParentHomeAcademySummary() {
  return requestJson("/parent/summary/");
}

export function activateHomeAcademyRegistration(registrationId) {
  return requestJson(`/offering-enrollments/${registrationId}/activate/`, {
    method: "POST",
    body: {},
  });
}

export function completeHomeAcademyRegistration(registrationId, payload) {
  return requestJson(`/offering-enrollments/${registrationId}/complete/`, {
    method: "POST",
    body: payload,
  });
}

export function postHomeAcademyTranscript(registrationId) {
  return requestJson(`/offering-enrollments/${registrationId}/post-transcript/`, {
    method: "POST",
    body: {},
  });
}
