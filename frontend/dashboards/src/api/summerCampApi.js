import { apiFetch } from "../lib/api";

const BASE = "/api/v1/summer-camp";

async function requestJson(path, { method = "GET", body, headers } = {}) {
  const response = await apiFetch(`${BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return response.json();
}

export async function fetchSummerCampConfig() {
  return requestJson("/config/");
}

export async function saveSummerCampConfig(data) {
  return requestJson("/config/", { method: "PUT", body: data });
}

export async function fetchSummerCampWizard() {
  return requestJson("/wizard/setup/");
}

export async function submitSummerCampWizard(data) {
  return requestJson("/wizard/setup/", { method: "POST", body: data });
}

export async function fetchSummerCampSessions() {
  return requestJson("/sessions/");
}

export async function fetchSummerCampSessionRoster(sessionId) {
  return requestJson(`/sessions/${sessionId}/roster/`);
}

export async function fetchSummerCampRosterToday() {
  return requestJson("/roster/today/");
}

export async function createSummerCampEnrollment(payload) {
  return requestJson("/enrollments/", { method: "POST", body: payload });
}

export async function fetchSummerCampEnrollments(params = {}) {
  const query = new URLSearchParams(params).toString();
  const path = query ? `/enrollments/?${query}` : "/enrollments/";
  return requestJson(path);
}

export async function checkinSummerCamper(payload) {
  return requestJson("/attendance/checkin/", { method: "POST", body: payload });
}

export async function checkoutSummerCamper(payload) {
  return requestJson("/attendance/checkout/", { method: "POST", body: payload });
}

export async function fetchSummerCampIncidents() {
  return requestJson("/incidents/");
}

export async function createSummerCampIncident(payload) {
  return requestJson("/incidents/", { method: "POST", body: payload });
}

export async function fetchSummerCampMissingForms() {
  return requestJson("/forms/missing/");
}

export async function fetchSummerCampHealthReviewQueue() {
  return requestJson("/health/review-queue/");
}

export async function fetchSummerCampParentSummary(studentId) {
  return requestJson(`/parent/${studentId}/`);
}

export async function fetchSummerCampBoardSummary() {
  return requestJson("/board/summary/");
}
