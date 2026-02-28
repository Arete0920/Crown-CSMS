/**
 * financeSetupApi.js
 * ==================
 * Crown Finance Setup Wizard — API helpers.
 *
 * Base URL: /api/v1/finance-setup/
 * Auth:     sessionStorage("crown.jwt.access") + X-School-ID header
 */

const BASE = "/api/v1/finance-setup";

function getToken() {
  return sessionStorage.getItem("crown.jwt.access") || "";
}

function getSchoolId() {
  return sessionStorage.getItem("crown.school.id") || "1";
}

function headers(extra = {}) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getToken()}`,
    "X-School-ID": getSchoolId(),
    ...extra,
  };
}

/**
 * Fetch the current policy status for a given academic year.
 * Returns null (not 404 throw) if no policy exists yet.
 */
export async function fetchFinanceStatus(year) {
  const resp = await fetch(`${BASE}/wizard/status/?year=${encodeURIComponent(year)}`, {
    method: "GET",
    headers: headers(),
  });

  if (resp.status === 404) return null;
  if (!resp.ok) throw new Error(`Finance status fetch failed: ${resp.status}`);
  return resp.json();
}

/**
 * Save (upsert) the full finance policy.
 * Throws with {status: 409} if the policy is already locked.
 */
export async function saveFinancePolicy(payload) {
  const resp = await fetch(`${BASE}/wizard/configure/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify(payload),
  });

  if (resp.status === 409) {
    const err = new Error("Policy is locked and cannot be edited.");
    err.status = 409;
    throw err;
  }
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body?.error || `Configure failed: ${resp.status}`);
  }
  return resp.json();
}

/**
 * Permanently lock the finance policy for a given academic year.
 */
export async function lockFinancePolicy(year, lockedBy = "") {
  const resp = await fetch(`${BASE}/wizard/lock/`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ academic_year: year, locked_by: lockedBy }),
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body?.error || `Lock failed: ${resp.status}`);
  }
  return resp.json();
}

/**
 * Fetch the read-only snapshot (same data as status, different presentation intent).
 */
export async function fetchSnapshot(year) {
  const resp = await fetch(`${BASE}/wizard/snapshot/?year=${encodeURIComponent(year)}`, {
    method: "GET",
    headers: headers(),
  });
  if (resp.status === 404) return null;
  if (!resp.ok) throw new Error(`Snapshot fetch failed: ${resp.status}`);
  return resp.json();
}
