/**
 * financeSetupApi.js
 * ==================
 * Crown Finance Setup Wizard - API helpers.
 */
import { crownApiClient } from "./client";

const BASE = "/api/v1/finance-setup";

async function request(config) {
  return crownApiClient.request({
    validateStatus: () => true,
    ...config,
  });
}

function responseData(response) {
  return response.data ?? null;
}

function responseError(response, fallbackMessage) {
  const err = new Error(response.data?.error || fallbackMessage);
  err.status = response.status;
  err.body = response.data ?? null;
  err.url = response.config?.url || "";
  return err;
}

/**
 * Fetch the current policy status for a given academic year.
 * Returns null (not 404 throw) if no policy exists yet.
 */
export async function fetchFinanceStatus(year) {
  const response = await request({
    method: "GET",
    url: `${BASE}/wizard/status/?year=${encodeURIComponent(year)}`,
  });

  if (response.status === 404) return null;
  if (response.status < 200 || response.status >= 300) {
    throw responseError(response, `Finance status fetch failed: ${response.status}`);
  }
  return responseData(response);
}

/**
 * Save (upsert) the full finance policy.
 * Throws with {status: 409} if the policy is already locked.
 */
export async function saveFinancePolicy(payload) {
  const response = await request({
    method: "POST",
    url: `${BASE}/wizard/configure/`,
    data: payload,
  });

  if (response.status === 409) {
    const err = new Error("Policy is locked and cannot be edited.");
    err.status = 409;
    err.body = response.data ?? null;
    err.url = response.config?.url || "";
    throw err;
  }
  if (response.status < 200 || response.status >= 300) {
    throw responseError(response, `Configure failed: ${response.status}`);
  }
  return responseData(response);
}

/**
 * Permanently lock the finance policy for a given academic year.
 */
export async function lockFinancePolicy(year, lockedBy = "") {
  const response = await request({
    method: "POST",
    url: `${BASE}/wizard/lock/`,
    data: { academic_year: year, locked_by: lockedBy },
  });

  if (response.status < 200 || response.status >= 300) {
    throw responseError(response, `Lock failed: ${response.status}`);
  }
  return responseData(response);
}

/**
 * Fetch the read-only snapshot (same data as status, different presentation intent).
 */
export async function fetchSnapshot(year) {
  const response = await request({
    method: "GET",
    url: `${BASE}/wizard/snapshot/?year=${encodeURIComponent(year)}`,
  });

  if (response.status === 404) return null;
  if (response.status < 200 || response.status >= 300) {
    throw responseError(response, `Snapshot fetch failed: ${response.status}`);
  }
  return responseData(response);
}
