import { authenticatedFetch, getAccessToken, getSelectedSchoolId } from "../utils/authClient";

// Compatibility exports retained for GradebookRO; authClient owns storage access.
export function getToken() {
  return getAccessToken();
}

export function getSchoolId() {
  return getSelectedSchoolId();
}

// Single canonical application API path.
export async function apiFetch(path, opts = {}) {
  return authenticatedFetch(path, opts);
}
