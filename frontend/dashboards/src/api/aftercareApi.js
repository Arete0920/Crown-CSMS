/**
 * Aftercare API helpers.
 * All requests use the shared auth + school header path.
 */
import { apiFetch } from "../lib/api";

const BASE = "/api/v1/aftercare";

async function requestJson(path, { method = "GET", body, headers } = {}) {
  const response = await apiFetch(`${BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(headers || {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  return response.json();
}

// Program config
export async function fetchAftercareConfig() {
  return requestJson("/config/");
}

export async function saveAftercareConfig(data) {
  return requestJson("/config/", { method: "PUT", body: data });
}

// Wizard
export async function fetchWizardConfig() {
  return requestJson("/wizard/setup/");
}

export async function submitWizardConfig(data) {
  return requestJson("/wizard/setup/", { method: "POST", body: data });
}

// Enrollments
export async function fetchEnrollments() {
  return requestJson("/enrollments/");
}

export async function createEnrollment(data) {
  return requestJson("/enrollments/", { method: "POST", body: data });
}

// Pickup contacts
export async function fetchPickupContacts(studentId) {
  return requestJson(`/students/${studentId}/pickup-contacts/`);
}

// Today's roster
export async function fetchRosterToday() {
  return requestJson("/roster/today/");
}

// Check in/out
export async function checkinStudent(payload) {
  return requestJson("/attendance/checkin/", { method: "POST", body: payload });
}

export async function checkoutStudent(payload) {
  return requestJson("/attendance/checkout/", { method: "POST", body: payload });
}

// Incidents
export async function fetchIncidents() {
  return requestJson("/incidents/");
}

export async function createIncident(data) {
  return requestJson("/incidents/", { method: "POST", body: data });
}

// Board summary (no PII)
export async function getAftercareBoardSummary({ token, schoolId } = {}) {
  return requestJson("/board/summary/", {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(schoolId ? { "X-School-Id": String(schoolId) } : {}),
    },
  });
}
