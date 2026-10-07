/**
 * Canonical frontend API transport.
 *
 * Owns API-base resolution, authentication, tenant context, correlation IDs,
 * timeout/cancellation, credentials, and structured failures. Feature modules
 * should not duplicate this behavior.
 */

const TOKEN_KEY = "crown.jwt.access";
const SCHOOL_KEY = "crown.school.id";
const DEFAULT_TIMEOUT_MS = 15000;

function normalizeApiBaseUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function getApiBaseUrl() {
  return normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
}

function createCorrelationId() {
  try {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  } catch {
    // Fall through to a deterministic-format local identifier.
  }
  return `crown-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function isAbsoluteHttpUrl(value) {
  return typeof value === "string" && /^https?:\/\//i.test(value);
}

function isSameBrowserOrigin(value) {
  if (!isAbsoluteHttpUrl(value) || typeof window === "undefined") return false;
  try {
    return new URL(value).origin === window.location.origin;
  } catch {
    return false;
  }
}

function isConfiguredApiUrl(value) {
  const apiBase = getApiBaseUrl();
  if (!apiBase || !isAbsoluteHttpUrl(value)) return false;
  try {
    const requestUrl = new URL(value);
    const configuredUrl = new URL(apiBase);
    const configuredPath = configuredUrl.pathname.replace(/\/+$/, "");
    const pathMatches = configuredPath === ""
      || requestUrl.pathname === configuredPath
      || requestUrl.pathname.startsWith(`${configuredPath}/`);
    return requestUrl.origin === configuredUrl.origin && pathMatches;
  } catch {
    return false;
  }
}

function headersToObject(headers) {
  const values = {};
  headers?.forEach?.((value, key) => {
    values[key] = value;
  });
  return values;
}

function parseResponseBody(text, contentType = "") {
  if (!text) return null;
  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }
  return text;
}

function tokenFromStoredAuth(raw) {
  if (!raw) return "";
  try {
    const parsed = JSON.parse(raw);
    return parsed?.access_token || parsed?.access || parsed?.token || "";
  } catch {
    return "";
  }
}

function getCookie(name) {
  if (typeof document === "undefined") return "";
  const prefix = `${name}=`;
  for (const part of document.cookie.split(";")) {
    const value = part.trim();
    if (value.startsWith(prefix)) return decodeURIComponent(value.slice(prefix.length));
  }
  return "";
}

function methodNeedsCsrf(method) {
  return !["GET", "HEAD", "OPTIONS", "TRACE"].includes(String(method || "GET").toUpperCase());
}

export function resolveApiUrl(input) {
  if (typeof input !== "string" || isAbsoluteHttpUrl(input)) return input;
  const apiBase = getApiBaseUrl();
  if (!apiBase) return input;
  const path = input.startsWith("/") ? input : `/${input}`;
  return `${apiBase}${path}`;
}

export function buildApiUrl(input, query = {}) {
  const resolved = resolveApiUrl(input);
  if (typeof resolved !== "string") return resolved;
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost";
  const url = new URL(resolved, origin);
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    url.searchParams.set(key, String(value));
  });
  if (!isAbsoluteHttpUrl(resolved) && !getApiBaseUrl()) {
    return `${url.pathname}${url.search}${url.hash}`;
  }
  return url.toString();
}

export function getSelectedSchoolId() {
  try {
    const session = sessionStorage.getItem(SCHOOL_KEY);
    if (session) return session;
    return localStorage.getItem("schoolId") || localStorage.getItem(SCHOOL_KEY) || "";
  } catch {
    return "";
  }
}

export function setSelectedSchoolId(schoolId) {
  try {
    const value = String(schoolId || "").trim();
    if (value) sessionStorage.setItem(SCHOOL_KEY, value);
    else sessionStorage.removeItem(SCHOOL_KEY);
  } catch (error) {
    console.error(error);
  }
}

export function clearSelectedSchoolId() {
  setSelectedSchoolId("");
}

export function getAccessToken() {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
      || sessionStorage.getItem("crown_auth_token")
      || sessionStorage.getItem("access_token")
      || tokenFromStoredAuth(sessionStorage.getItem("crown_auth"))
      || "";
  } catch {
    return "";
  }
}

export function setAccessToken(token) {
  try {
    if (token) sessionStorage.setItem(TOKEN_KEY, token);
    else sessionStorage.removeItem(TOKEN_KEY);
  } catch (error) {
    console.error(error);
  }
}

export function clearAccessToken() {
  setAccessToken("");
}

export async function authenticatedFetch(input, init = {}) {
  const {
    timeoutMs = DEFAULT_TIMEOUT_MS,
    signal,
    query,
    correlationId = createCorrelationId(),
    validateStatus = (status) => status >= 200 && status < 300,
    ...requestInit
  } = init;

  const relativeApiInput = typeof input === "string" && !isAbsoluteHttpUrl(input);
  const resolvedInput = typeof input === "string" ? buildApiUrl(input, query) : input;
  const trustedApiRequest = relativeApiInput
    || (typeof resolvedInput === "string" && (
      isSameBrowserOrigin(resolvedInput) || isConfiguredApiUrl(resolvedInput)
    ));
  const headers = new Headers(requestInit.headers || {});

  if (trustedApiRequest) {
    const token = getAccessToken();
    if (token && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${token}`);
    const schoolId = getSelectedSchoolId();
    if (schoolId && !headers.has("X-School-Id")) headers.set("X-School-Id", schoolId);
    if (methodNeedsCsrf(requestInit.method)) {
      const csrfToken = getCookie("csrftoken");
      if (csrfToken && !headers.has("X-CSRFToken")) headers.set("X-CSRFToken", csrfToken);
    }
    const sameOriginCorrelation = !getApiBaseUrl()
      || (typeof resolvedInput === "string" && isSameBrowserOrigin(resolvedInput));
    if (!sameOriginCorrelation) {
      headers.delete("X-Correlation-Id");
    } else if (!headers.has("X-Correlation-Id")) {
      headers.set("X-Correlation-Id", correlationId);
    }
  }

  const controller = new AbortController();
  let timedOut = false;
  const timeoutId = timeoutMs > 0 ? setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs) : null;

  const abortFromCaller = () => controller.abort();
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", abortFromCaller, { once: true });
  }

  try {
    const response = await globalThis.fetch(resolvedInput, {
      ...requestInit,
      headers,
      credentials: trustedApiRequest ? (requestInit.credentials ?? "include") : requestInit.credentials,
      signal: controller.signal,
    });
    if (!validateStatus(response.status)) {
      const text = await response.text().catch(() => "");
      const contentType = response.headers?.get?.("content-type") || "";
      const data = parseResponseBody(text, contentType);
      const error = new Error(`HTTP ${response.status} ${response.statusText}`);
      error.status = response.status;
      error.url = typeof resolvedInput === "string" ? resolvedInput : (resolvedInput?.url || "");
      error.body = text.slice(0, 2000);
      error.correlationId = response.headers?.get?.("x-correlation-id") || correlationId;
      error.response = {
        status: response.status,
        statusText: response.statusText,
        data,
        headers: headersToObject(response.headers),
      };
      throw error;
    }
    return response;
  } catch (error) {
    if (error?.name === "AbortError") {
      error.timedOut = timedOut;
      error.correlationId = correlationId;
    }
    throw error;
  } finally {
    if (timeoutId) clearTimeout(timeoutId);
    if (signal) signal.removeEventListener("abort", abortFromCaller);
  }
}

export async function authenticatedJson(input, init = {}) {
  const response = await authenticatedFetch(input, init);
  const contentType = response.headers?.get?.("content-type") || "";
  if (contentType.includes("application/json")) return response.json();
  return response.text();
}

export async function jwtLogin({ username, password, apiBase = "" }) {
  const base = normalizeApiBaseUrl(apiBase || getApiBaseUrl());
  const response = await globalThis.fetch(`${base}/api/v1/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Login failed (${response.status}): ${text}`);
  }
  const data = await response.json();
  if (!data?.access) throw new Error("Login response missing access token");
  setAccessToken(data.access);
  return data;
}
