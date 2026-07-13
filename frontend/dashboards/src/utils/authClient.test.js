import { afterEach, describe, expect, it, vi } from "vitest";
import { resolveApiUrl } from "./authClient";

describe("resolveApiUrl", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
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
});
