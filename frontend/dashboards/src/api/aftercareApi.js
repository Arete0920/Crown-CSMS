/**
 * Aftercare API helpers.
 * All requests include X-School-ID header (canonical tenant pattern).
 */

function getSession() {
  try {
    return {
      token: sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id") || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}

function headers() {
  const { token, schoolId } = getSession();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(schoolId ? { "X-School-ID": schoolId } : {}),
  };
}

const BASE = "/api/v1/aftercare";

// Program config
export async function fetchAftercareConfig() {
  const r = await fetch(`${BASE}/config/`, { headers: headers() });
  if (!r.ok) throw new Error(`aftercare config: ${r.status}`);
  return r.json();
}

export async function saveAftercareConfig(data) {
  const r = await fetch(`${BASE}/config/`, {
    method: "PUT",
    headers: headers(),
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`aftercare config save: ${r.status}`);
  return r.json();
}

// Wizard
export async function fetchWizardConfig() {
  const r = await fetch(`${BASE}/wizard/setup/`, { headers: headers() });
  if (!r.ok) throw new Error(`aftercare wizard: ${r.status}`);
  return r.json();
}

export async function submitWizardConfig(data) {
  const r = await fetch(`${BASE}/wizard/setup/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`aftercare wizard submit: ${r.status}`);
  return r.json();
}

// Enrollments
export async function fetchEnrollments() {
  const r = await fetch(`${BASE}/enrollments/`, { headers: headers() });
  if (!r.ok) throw new Error(`aftercare enrollments: ${r.status}`);
  return r.json();
}

export async function createEnrollment(data) {
  const r = await fetch(`${BASE}/enrollments/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`aftercare enrollment create: ${r.status}`);
  return r.json();
}

// Pickup contacts
export async function fetchPickupContacts(studentId) {
  const r = await fetch(`${BASE}/students/${studentId}/pickup-contacts/`, { headers: headers() });
  if (!r.ok) throw new Error(`aftercare pickup contacts: ${r.status}`);
  return r.json();
}

// Today's roster
export async function fetchRosterToday() {
  const r = await fetch(`${BASE}/roster/today/`, { headers: headers() });
  if (!r.ok) throw new Error(`aftercare roster: ${r.status}`);
  return r.json();
}

// Check in/out
export async function checkinStudent(payload) {
  const r = await fetch(`${BASE}/attendance/checkin/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`aftercare checkin: ${r.status}`);
  return r.json();
}

export async function checkoutStudent(payload) {
  const r = await fetch(`${BASE}/attendance/checkout/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`aftercare checkout: ${r.status}`);
  return r.json();
}

// Incidents
export async function fetchIncidents() {
  const r = await fetch(`${BASE}/incidents/`, { headers: headers() });
  if (!r.ok) throw new Error(`aftercare incidents: ${r.status}`);
  return r.json();
}

export async function createIncident(data) {
  const r = await fetch(`${BASE}/incidents/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(data),
  });
  if (!r.ok) throw new Error(`aftercare incident create: ${r.status}`);
  return r.json();
}

// Board summary (no PII)
export async function getAftercareBoardSummary({ token, schoolId } = {}) {
  const hdrs = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(schoolId ? { "X-School-ID": schoolId } : {}),
  };
  const r = await fetch(`${BASE}/board/summary/`, { headers: hdrs });
  if (!r.ok) throw new Error(`aftercare board summary: ${r.status}`);
  return r.json();
}
