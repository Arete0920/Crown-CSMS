/**
 * api/onboarding.js
 *
 * Uses the shared apiFetch client while keeping the existing absolute URL shape
 * and JSON/null response parsing behavior for the onboarding import flow.
 */
import { apiFetch } from "../lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (response.status === 204 || !contentType.includes("application/json")) {
    return null;
  }
  return response.json();
}

/** Step 1: create an ImportSession with the chosen mode */
export async function createImportSession(mode) {
  const response = await apiFetch(`${API_BASE}/api/v1/onboarding/imports/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  return parseResponse(response);
}

/** Step 2: upload the CSV file to an existing session */
export async function uploadImportFile(importId, file) {
  const form = new FormData();
  form.append("file", file);
  const response = await apiFetch(`${API_BASE}/api/v1/onboarding/imports/${importId}/upload/`, {
    method: "POST",
    body: form,
  });
  return parseResponse(response);
}

/** Step 3: trigger server-side validation */
export async function validateImport(importId) {
  const response = await apiFetch(`${API_BASE}/api/v1/onboarding/imports/${importId}/validate/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return parseResponse(response);
}

/** Step 4: fetch summary + sample rows for preview */
export async function previewImport(importId) {
  const response = await apiFetch(`${API_BASE}/api/v1/onboarding/imports/${importId}/preview/`, {
    method: "GET",
  });
  return parseResponse(response);
}

/** Step 5: commit the import (requires confirm flag) */
export async function commitImport(importId) {
  const response = await apiFetch(`${API_BASE}/api/v1/onboarding/imports/${importId}/commit/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
  return parseResponse(response);
}

/** Step 6: verify results post-commit */
export async function verifyImport(importId) {
  const response = await apiFetch(`${API_BASE}/api/v1/onboarding/imports/${importId}/verify/`, {
    method: "GET",
  });
  return parseResponse(response);
}
