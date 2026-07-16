import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  authenticatedFetch,
  authenticatedJson,
  buildApiUrl,
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

  it("adds auth, tenant, correlation, credentials, and query to relative API calls", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://crown-api-prod.azurewebsites.net");
    const response = new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(response);
    await authenticatedFetch("/api/v1/dashboards/teacher/summary", {
      query: { term: "fall" },
      correlationId: "corr-123",
    });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      "https://crown-api-prod.azurewebsites.net/api/v1/dashboards/teacher/summary?term=fall",
    );
    expect(init.credentials).toBe("include");
    expect(init.headers.get("Authorization")).toBe("Bearer token-123");
    expect(init.headers.get("X-School-Id")).toBe("school-123");
    expect(init.headers.get("X-Correlation-Id")).toBe("corr-123");
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
});
