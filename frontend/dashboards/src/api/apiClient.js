// frontend/dashboards/src/api/apiClient.js
// Authenticated API client hook — Bearer token + X-School-Id header.
//
// Usage:
//   const { request } = useApiClient();
//   const data = await request("/api/dashboards/summary/");
import { useApiToken } from "../auth/useApiToken";

/**
 * Returns a `request(path, opts)` function wired with auth headers.
 * Throws on non-2xx responses with a descriptive error message.
 */
export function useApiClient() {
  const getToken = useApiToken();

  async function request(path, opts = {}) {
    const token = await getToken();

    const headers = new Headers(opts.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    headers.set("Accept", "application/json");

    // Tenant header: required by all Crown API endpoints.
    const schoolId =
      sessionStorage.getItem("crown.school.id") ||
      localStorage.getItem("X_SCHOOL_ID") ||
      "";

    if (!schoolId) {
      throw new Error(
        "Missing school context. Set crown.school.id in sessionStorage after login."
      );
    }
    headers.set("X-School-Id", schoolId);

    const res = await fetch(path, {
      ...opts,
      headers,
      credentials: "include",
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`API ${path} → ${res.status}: ${text}`);
    }

    return res.json();
  }

  return { request };
}
