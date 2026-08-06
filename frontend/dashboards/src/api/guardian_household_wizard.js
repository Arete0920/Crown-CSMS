/**
 * api/guardian_household_wizard.js
 *
 * Uses the shared apiFetch client for auth and school scoping.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";
const PREFIX = `${API_BASE}/api/v1/guardian-household-wizard/sessions`;

/** Step 1: create session */
export async function createGuardianHouseholdSession() {
  const url = `${PREFIX}/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
}

/** Step 2: configure household
 * @param {object} household_data - {name, address: {street, city, state, zip}}
 */
export async function configureGuardianHouseholdSession(sessionId, household_data) {
  const url = `${PREFIX}/${sessionId}/configure/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ household_data }),
  });
}

/** Step 3: add guardians
 * @param {Array} guardian_data - [{name, email, custody_type, contact_priority, receives_communications}]
 */
export async function addGuardians(sessionId, guardian_data) {
  const url = `${PREFIX}/${sessionId}/add_guardians/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ guardian_data }),
  });
}

/** Step 4: link students
 * @param {Array} link_data - [{student_id, relationship}]
 */
export async function linkStudents(sessionId, link_data) {
  const url = `${PREFIX}/${sessionId}/link_students/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ link_data }),
  });
}

/** Step 5: commit */
export async function commitGuardianHouseholdSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/commit/`;
  return apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
}

/** Step 6: verify */
export async function verifyGuardianHouseholdSession(sessionId) {
  const url = `${PREFIX}/${sessionId}/verify/`;
  return apiFetch(url, { method: "GET" });
}
