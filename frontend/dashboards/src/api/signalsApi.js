/**
 * signals API helpers - Crown Signal Engine + Intervention Workflow
 *
 * Auth pattern: shared apiFetch with optional explicit token + school header
 * overrides for board/staff endpoints.
 */
import { apiFetch } from "../lib/api";

async function safeJson(response) {
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function makeHeaders({ token, schoolId }) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (schoolId) headers["X-School-Id"] = String(schoolId);
  return headers;
}

// Board read-only
export async function fetchBoardCompass({ token, schoolId }) {
  const response = await apiFetch("/api/v1/signals/board/compass/", {
    headers: makeHeaders({ token, schoolId }),
  });
  return safeJson(response);
}

export async function fetchBoardRiskCounts({ token, schoolId }) {
  const response = await apiFetch("/api/v1/signals/board/risk-counts/", {
    headers: makeHeaders({ token, schoolId }),
  });
  return safeJson(response);
}

// Staff endpoints
export async function fetchStudentSignals({ token, schoolId, studentId }) {
  const response = await apiFetch(`/api/v1/signals/students/${studentId}/signals/`, {
    headers: makeHeaders({ token, schoolId }),
  });
  return safeJson(response);
}

export async function fetchInterventionCases({ token, schoolId }) {
  const response = await apiFetch("/api/v1/signals/interventions/cases/", {
    headers: makeHeaders({ token, schoolId }),
  });
  return (await safeJson(response)) ?? [];
}

export async function postInterventionAction({ token, schoolId, caseId, payload }) {
  const response = await apiFetch(`/api/v1/signals/interventions/cases/${caseId}/actions/`, {
    method: "POST",
    headers: makeHeaders({ token, schoolId }),
    body: JSON.stringify(payload),
  });
  return safeJson(response);
}
