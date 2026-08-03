import { beforeEach, describe, expect, it, vi } from "vitest";

const { authenticatedFetch } = vi.hoisted(() => ({
  authenticatedFetch: vi.fn(),
}));

vi.mock("../utils/authClient.js", () => ({
  authenticatedFetch,
}));

import {
  fetchDashboardAlerts,
  fetchDashboardDrilldown,
  fetchDashboardMe,
  fetchDashboardSummary,
} from "./dashboards.js";

function response(body, status = 200, headers = {}) {
  return {
    status,
    headers: new Headers(headers),
    json: vi.fn().mockResolvedValue(body),
  };
}

describe("dashboard API client", () => {
  beforeEach(() => {
    authenticatedFetch.mockReset();
  });

  it("routes dashboard summary through authenticatedFetch and preserves response shape", async () => {
    authenticatedFetch.mockResolvedValue(
      response({ widgets: [] }, 200, { "x-correlation-id": "corr-1" }),
    );

    await expect(fetchDashboardSummary("school-123")).resolves.toEqual({
      ok: true,
      status: 200,
      data: { widgets: [] },
      correlationId: "corr-1",
      error: "",
    });

    expect(authenticatedFetch).toHaveBeenCalledWith("/api/dashboards/summary/", {
      credentials: "include",
      method: "GET",
      headers: {
        "X-School-Id": "school-123",
      },
    });
  });

  it("uses the canonical client for all dashboard endpoints without forwarding demo role authority", async () => {
    authenticatedFetch.mockResolvedValue(response({ ok: true }));

    // Extra legacy role arguments are intentionally ignored by the production client.
    await fetchDashboardMe("school", "admin");
    await fetchDashboardDrilldown("attendance", "school", "admin");
    await fetchDashboardAlerts("school", "admin");

    expect(authenticatedFetch.mock.calls.map(([url]) => url)).toEqual([
      "/api/dashboards/me/",
      "/api/dashboards/drilldown/?widget=attendance",
      "/api/dashboards/alerts/",
    ]);
    expect(authenticatedFetch.mock.calls.map(([, init]) => init.headers)).toEqual([
      { "X-School-Id": "school" },
      { "X-School-Id": "school" },
      { "X-School-Id": "school" },
    ]);
    expect(
      authenticatedFetch.mock.calls.some(([, init]) => Object.hasOwn(init.headers, "X-Demo-Role")),
    ).toBe(false);
  });

  it("normalizes structured failures without throwing", async () => {
    const error = new Error("HTTP 403 Forbidden");
    error.status = 403;
    error.body = JSON.stringify({ detail: "Not authorized" });
    authenticatedFetch.mockRejectedValue(error);

    await expect(fetchDashboardSummary("school")).resolves.toEqual({
      ok: false,
      status: 403,
      data: { detail: "Not authorized" },
      correlationId: "",
      error: "Not authorized",
    });
  });
});
