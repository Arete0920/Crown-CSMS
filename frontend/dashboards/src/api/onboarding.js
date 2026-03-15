/**
 * api/onboarding.js
 *
 * Follows the api/admissions.js pattern exactly:
 *  - getToken / getSchoolId from ../lib/api
 *  - const API_BASE from VITE_API_BASE_URL
 *  - raw fetch() with manual Authorization + X-School-Id headers
 *  - explicit .json() parsing
 *  - structured error throw: { status, body, url }
 */
import { getToken, getSchoolId } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

function headers(extra = {}) {
  return {
    Authorization: `Bearer ${getToken()}`,
    "X-School-Id": getSchoolId(),
    ...extra,
  };
}

async function checkResponse(res, url) {
  if (!res.ok) {
    let body = null;
    try { body = await res.json(); } catch { /* ignore */ }
    const err = new Error(`HTTP ${res.status}`);
    err.status = res.status;
    err.body = body;
    err.url = url;
    throw err;
  }
  // 204 No Content or empty body â€” return null instead of throwing a JSON parse error
  const ct = res.headers.get("content-type") || "";
  if (res.status === 204 || !ct.includes("application/json")) return null;
  return res.json();
}

/** Step 1: create an ImportSession with the chosen mode */
export async function createImportSession(mode) {
  const url = `${API_BASE}/api/v1/onboarding/imports/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ mode }),
  });
  return checkResponse(res, url);
}

/** Step 2: upload the CSV file to an existing session */
export async function uploadImportFile(importId, file) {
  const url = `${API_BASE}/api/v1/onboarding/imports/${importId}/upload/`;
  const form = new FormData();
  form.append("file", file);
  // Do NOT set Content-Type â€” browser sets multipart/form-data + boundary
  const res = await fetch(url, {
    method: "POST",
    headers: headers(),   // no Content-Type override
    body: form,
  });
  return checkResponse(res, url);
}

/** Step 3: trigger server-side validation */
export async function validateImport(importId) {
  const url = `${API_BASE}/api/v1/onboarding/imports/${importId}/validate/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({}),
  });
  return checkResponse(res, url);
}

/** Step 4: fetch summary + sample rows for preview */
export async function previewImport(importId) {
  const url = `${API_BASE}/api/v1/onboarding/imports/${importId}/preview/`;
  const res = await fetch(url, {
    method: "GET",
    headers: headers(),
  });
  return checkResponse(res, url);
}

/** Step 5: commit the import (requires confirm flag) */
export async function commitImport(importId) {
  const url = `${API_BASE}/api/v1/onboarding/imports/${importId}/commit/`;
  const res = await fetch(url, {
    method: "POST",
    headers: headers({ "Content-Type": "application/json" }),
    body: JSON.stringify({ confirm: true }),
  });
  return checkResponse(res, url);
}

/** Step 6: verify results post-commit */
export async function verifyImport(importId) {
  const url = `${API_BASE}/api/v1/onboarding/imports/${importId}/verify/`;
  const res = await fetch(url, {
    method: "GET",
    headers: headers(),
  });
  return checkResponse(res, url);
}

