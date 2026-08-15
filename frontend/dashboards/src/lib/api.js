import { authenticatedFetch, getAccessToken, getSelectedSchoolId } from "../utils/authClient";
import { authenticatedJson } from "../utils/authClient";

// Compatibility exports retained for GradebookRO; authClient owns storage access.
export function getToken() {
  return getAccessToken();
}

export function getSchoolId() {
  return getSelectedSchoolId();
}

// Single canonical application API path for callers that need the raw Response.
export async function apiFetch(path, opts = {}) {
  return authenticatedFetch(path, opts);
}

// Canonical JSON application API path for callers that consume response payload fields.
export async function apiJson(path, opts = {}) {
  return authenticatedJson(path, opts);
}
