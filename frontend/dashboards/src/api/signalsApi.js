/**
 * signals API helpers — Crown Signal Engine + Intervention Workflow
 *
 * Auth pattern: sessionStorage JWT + X-School-Id header (matches all Crown dashboards).
 * All fetches are GET-only for board endpoints; staff endpoints support POST.
 */

async function safeJson(res) {
  const text = await res.text();
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function makeHeaders({ token, schoolId }) {
  const h = { "Content-Type": "application/json" };
  if (token)    h.Authorization = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = String(schoolId);
  return h;
}

// ── Board read-only ─────────────────────────────────────────────────────────

export async function fetchBoardCompass({ token, schoolId }) {
  const res = await fetch("/api/v1/signals/board/compass/", {
    headers: makeHeaders({ token, schoolId }),
  });
  return res.ok ? await safeJson(res) : null;
}

export async function fetchBoardRiskCounts({ token, schoolId }) {
  const res = await fetch("/api/v1/signals/board/risk-counts/", {
    headers: makeHeaders({ token, schoolId }),
  });
  return res.ok ? await safeJson(res) : null;
}

// ── Staff endpoints ─────────────────────────────────────────────────────────

export async function fetchStudentSignals({ token, schoolId, studentId }) {
  const res = await fetch(`/api/v1/signals/students/${studentId}/signals/`, {
    headers: makeHeaders({ token, schoolId }),
  });
  return res.ok ? await safeJson(res) : null;
}

export async function fetchInterventionCases({ token, schoolId }) {
  const res = await fetch("/api/v1/signals/interventions/cases/", {
    headers: makeHeaders({ token, schoolId }),
  });
  return res.ok ? await safeJson(res) : [];
}

export async function postInterventionAction({ token, schoolId, caseId, payload }) {
  const res = await fetch(`/api/v1/signals/interventions/cases/${caseId}/actions/`, {
    method: "POST",
    headers: makeHeaders({ token, schoolId }),
    body: JSON.stringify(payload),
  });
  return res.ok ? await safeJson(res) : null;
}
