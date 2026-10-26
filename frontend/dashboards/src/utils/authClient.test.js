import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  authenticatedFetch,
  authenticatedJson,
  buildApiUrl,
  clearBrowserAuthState,
  getAccessToken,
  jwtLogin,
  resolveApiUrl,
} from "./authClient";

function memoryStorage(initial = {}) {
  const values = new Map(Object.entries(initial));
  return {
    getItem: vi.fn((key) => values.get(key) ?? null),
    setItem: vi.fn((key, value) => values.set(key, String(value))),
    removeItem: vi.fn((key) => values.delete(key)),
    clear: vi.fn(() => values.clear()),
  };
}

describe("canonical authenticated client", () => {
  beforeEach(() => {
    vi.stubGlobal("sessionStorage", memoryStorage({
      "crown.jwt.access": "token-123",
      "crown.school.id": "school-123",
    }));
    vi.stubGlobal("localStorage", memoryStorage());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("routes relative API paths through the configured Azure API base", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://crown-api-prod.azurewebsites.net/");
    expect(resolveApiUrl("/api/v1/dashboards/summary/")).toBe(
      "https://crown-api-prod.azurewebsites.net/api/v1/dashboards/summary/",
    );
  });

  it("normalizes whitespace and repeated trailing slashes", () => {
    vi.stubEnv("VITE_API_BASE_URL", "  https://crown-api-prod.azurewebsites.net///  ");
    expect(resolveApiUrl("api/health/")).toBe(
      "https://crown-api-prod.azurewebsites.net/api/health/",
    );
  });

  it("preserves absolute URLs", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://crown-api-prod.azurewebsites.net");
    expect(resolveApiUrl("https://example.com/api/health/")).toBe(
      "https://example.com/api/health/",
    );
  });

  it("preserves local relative behavior when no API base is configured", () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    expect(resolveApiUrl("/api/health/")).toBe("/api/health/");
  });

  it("builds query strings without losing configured API-base resolution", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://crown-api-prod.azurewebsites.net");
    expect(buildApiUrl("/api/v1/dashboards/teacher/summary", {
      term: "fall",
      empty: "",
      page: 2,
    })).toBe(
      "https://crown-api-prod.azurewebsites.net/api/v1/dashboards/teacher/summary?term=fall&page=2",
    );
  });

  it("adds auth, tenant, credentials, and query to configured cross-origin API calls without an unsupported correlation preflight header", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://crown-api-prod.azurewebsites.net");
    const response = new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: {
        "content-type": "application/json",
        "x-correlation-id": "server-corr",
      },
    });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
    await authenticatedFetch("/api/v1/dashboards/teacher/summary", {
      query: { term: "fall" },
      correlationId: "corr-123",
      headers: { "X-Correlation-Id": "caller-corr" },
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      "https://crown-api-prod.azurewebsites.net/api/v1/dashboards/teacher/summary?term=fall",
    );
    expect(init.credentials).toBe("include");
    expect(init.headers.get("Authorization")).toBe("Bearer token-123");
    expect(init.headers.get("X-School-Id")).toBe("school-123");
    expect(init.headers.has("X-Correlation-Id")).toBe(false);
  });

  it("retains client correlation headers when no API base is configured", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    const response = new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
    await authenticatedFetch("/api/v1/nav/", { correlationId: "corr-local" });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.get("X-Correlation-Id")).toBe("corr-local");
  });

  it("retains client correlation headers for a configured same-origin API base", async () => {
    vi.stubEnv("VITE_API_BASE_URL", window.location.origin);
    const response = new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
    await authenticatedFetch("/api/v1/nav/", { correlationId: "corr-same-origin" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`${window.location.origin}/api/v1/nav/`);
    expect(init.headers.get("X-Correlation-Id")).toBe("corr-same-origin");
  });

  it("ignores bearer tokens persisted in localStorage", async () => {
    vi.stubGlobal("sessionStorage", memoryStorage({
      "crown.school.id": "school-123",
    }));
    vi.stubGlobal("localStorage", memoryStorage({
      "crown.jwt.access": "persistent-token-must-not-be-used",
    }));

    const response = new Response("ok", { status: 200 });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(response);

    await authenticatedFetch("/api/v1/nav/");

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers.has("Authorization")).toBe(false);
    expect(init.headers.get("X-School-Id")).toBe("school-123");
  });

  it("does not forward Crown credentials or tenant context to caller-supplied external URLs", async () => {
    const response = new Response("ok", { status: 200 });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
    await authenticatedFetch("https://example.com/public.json", {
      correlationId: "corr-external",
    });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.credentials).toBeUndefined();
    expect(init.headers.has("Authorization")).toBe(false);
    expect(init.headers.has("X-School-Id")).toBe(false);
    expect(init.headers.has("X-Correlation-Id")).toBe(false);
  });

  it("normalizes HTTP failures with status, body, URL, and correlation ID", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://crown-api-prod.azurewebsites.net");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Forbidden" }), {
        status: 403,
        statusText: "Forbidden",
        headers: {
          "content-type": "application/json",
          "x-correlation-id": "server-corr",
        },
      }),
    );
    await expect(authenticatedFetch("/api/v1/nav/", {
      correlationId: "client-corr",
    })).rejects.toMatchObject({
      status: 403,
      body: JSON.stringify({ detail: "Forbidden" }),
      correlationId: "server-corr",
      url: "https://crown-api-prod.azurewebsites.net/api/v1/nav/",
    });
  });

  it("parses JSON payloads through the canonical transport", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ widgets: [] }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    await expect(authenticatedJson("/api/v1/dashboards/teacher/summary")).resolves.toEqual({
      widgets: [],
    });
  });

  it("propagates caller cancellation through the canonical request signal", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((_, init) => new Promise((resolve, reject) => {
      init.signal.addEventListener("abort", () => {
        const error = new Error("aborted");
        error.name = "AbortError";
        reject(error);
      }, { once: true });
    }));
    const controller = new AbortController();
    const request = authenticatedFetch("/api/v1/nav/", {
      signal: controller.signal,
      timeoutMs: 0,
      correlationId: "cancel-corr",
    });
    controller.abort();
    await expect(request).rejects.toMatchObject({
      name: "AbortError",
      timedOut: false,
      correlationId: "cancel-corr",
    });
  });

  it("clears the matching browser session on 401 and redirects to sign-in without retry", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    vi.stubEnv("VITE_DEMO_MODE", "");
    vi.stubEnv("VITE_SANDBOX_MODE", "");
    vi.stubEnv("VITE_WIZARD_CERTIFICATION", "");
    const replace = vi.fn();
    vi.stubGlobal("window", {
      location: { origin: "http://localhost", pathname: "/teacher", replace },
    });
    sessionStorage.setItem("crown.jwt.refresh", "synthetic-refresh");
    sessionStorage.setItem("crown_user", "synthetic-user");
    sessionStorage.setItem("access_token", "old-token");
    localStorage.setItem("crown_user", "old-user");
    localStorage.setItem("unrelated.draft", "preserve");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Invalid token" }), {
        status: 401,
        statusText: "Unauthorized",
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(authenticatedFetch("/api/v1/nav/")).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][1].headers.get("Authorization")).toBe("Bearer token-123");
    expect(getAccessToken()).toBe("");
    expect(sessionStorage.getItem("crown.jwt.refresh")).toBeNull();
    expect(sessionStorage.getItem("crown.school.id")).toBeNull();
    expect(localStorage.getItem("crown_user")).toBeNull();
    expect(localStorage.getItem("unrelated.draft")).toBe("preserve");
    expect(replace).toHaveBeenCalledExactlyOnceWith("/login?reason=session-expired");
  });

  it("ends a 401 session even when the API caller accepts all HTTP statuses", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    vi.stubEnv("VITE_DEMO_MODE", "");
    vi.stubEnv("VITE_SANDBOX_MODE", "");
    vi.stubEnv("VITE_WIZARD_CERTIFICATION", "");
    const replace = vi.fn();
    vi.stubGlobal("window", {
      location: { origin: "http://localhost", pathname: "/finance", replace },
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 401 }));

    const result = await authenticatedFetch("/api/v1/nav/", { validateStatus: () => true });
    expect(result.status).toBe(401);
    expect(getAccessToken()).toBe("");
    expect(replace).toHaveBeenCalledTimes(1);
  });

  it.each([403, 429, 503])("does not clear credentials or redirect for HTTP %s", async (status) => {
    const replace = vi.fn();
    vi.stubGlobal("window", {
      location: { origin: "http://localhost", pathname: "/teacher", replace },
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status }));
    await expect(authenticatedFetch("/api/v1/nav/")).rejects.toMatchObject({ status });
    expect(getAccessToken()).toBe("token-123");
    expect(replace).not.toHaveBeenCalled();
  });

  it("does not expire a newer login after a stale concurrent 401", async () => {
    const replace = vi.fn();
    vi.stubGlobal("window", {
      location: { origin: "http://localhost", pathname: "/teacher", replace },
    });
    vi.spyOn(globalThis, "fetch").mockImplementation(async () => {
      sessionStorage.setItem("crown.jwt.access", "new-session");
      return new Response(null, { status: 401 });
    });
    await expect(authenticatedFetch("/api/v1/nav/")).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBe("new-session");
    expect(replace).not.toHaveBeenCalled();
  });

  it("does not expire the user's session after an external origin returns 401", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 401 }));
    await expect(authenticatedFetch("https://external.example/api/data")).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBe("token-123");
  });

  it("does not redirect or clear tenant context for an anonymous 401", async () => {
    vi.stubGlobal("sessionStorage", memoryStorage({ "crown.school.id": "school-123" }));
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 401 }));
    await expect(authenticatedFetch("/api/v1/nav/")).rejects.toMatchObject({ status: 401 });
    expect(sessionStorage.getItem("crown.school.id")).toBe("school-123");
  });

  it("leaves the current session intact on a transport error", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("network unavailable"));
    await expect(authenticatedFetch("/api/v1/nav/")).rejects.toThrow("network unavailable");
    expect(getAccessToken()).toBe("token-123");
  });

  it("does not change explicit sandbox sessions on 401", async () => {
    vi.stubEnv("VITE_DEMO_MODE", "sandbox");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(null, { status: 401 }));
    await expect(authenticatedFetch("/api/v1/nav/")).rejects.toMatchObject({ status: 401 });
    expect(getAccessToken()).toBe("token-123");
  });

  it("clears legacy browser keys during explicit logout, preserving unrelated data", () => {
    sessionStorage.setItem("crown.jwt.refresh", "sandbox-refresh");
    sessionStorage.setItem("crown_auth_token", "legacy-token");
    localStorage.setItem("crown_user", "cached-user");
    localStorage.setItem("unrelated.draft", "keep");
    clearBrowserAuthState();
    expect(getAccessToken()).toBe("");
    expect(sessionStorage.getItem("crown.jwt.refresh")).toBeNull();
    expect(sessionStorage.getItem("crown_auth_token")).toBeNull();
    expect(localStorage.getItem("crown_user")).toBeNull();
    expect(localStorage.getItem("unrelated.draft")).toBe("keep");
  });

  it("does not store a SimpleJWT refresh token when using the shared login helper", async () => {
    sessionStorage.setItem("crown.jwt.refresh", "old-refresh");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ access: "new-access", refresh: "new-refresh" }), {
        status: 200, headers: { "content-type": "application/json" },
      }),
    );
    const payload = await jwtLogin({ username: "synthetic@example.invalid", password: "synthetic" });
    expect(payload.refresh).toBe("new-refresh");
    expect(getAccessToken()).toBe("new-access");
    expect(sessionStorage.getItem("crown.jwt.refresh")).toBeNull();
  });
});
