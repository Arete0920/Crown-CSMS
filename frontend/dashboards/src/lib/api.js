import {
  authenticatedFetch,
  authenticatedJson,
  getAccessToken,
  getSelectedSchoolId,
} from "../utils/authClient";

// Compatibility exports retained for GradebookRO; authClient owns storage access.
export function getToken() {
  return getAccessToken();
}

export function getSchoolId() {
  return getSelectedSchoolId();
}

function withJsonContentType(opts = {}) {
  if (typeof opts.body !== "string" || !opts.body.trim()) return opts;

  try {
    JSON.parse(opts.body);
  } catch {
    return opts;
  }

  const headers = new Headers(opts.headers || {});
  if (headers.has("Content-Type")) return opts;
  headers.set("Content-Type", "application/json");
  return { ...opts, headers };
}

// Single canonical application API path for callers that need the raw Response.
export async function apiFetch(path, opts = {}) {
  return authenticatedFetch(path, withJsonContentType(opts));
}

// Canonical JSON application API path for callers that consume response payload fields.
export async function apiJson(path, opts = {}) {
  return authenticatedJson(path, withJsonContentType(opts));
}
