// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import JirehSGODashboard from "./JirehSGODashboard.jsx";
import { authenticatedFetch, getAccessToken } from "../utils/authClient.js";

vi.mock("../utils/authClient.js", () => ({
  authenticatedFetch: vi.fn(),
  getAccessToken: vi.fn(),
}));
const response = (data) => ({ json: async () => data });
beforeEach(() => {
  getAccessToken.mockReturnValue("synthetic");
  authenticatedFetch.mockImplementation(async (url) =>
    url.endsWith("/organizations/")
      ? response({ organizations: [{ id: "org-1", name: "Synthetic SGO", role: "VIEWER" }],
        funds_status: "NONCASH_ONLY" })
      : response({ organization: { id: "org-1", name: "Synthetic SGO" },
        role: "VIEWER", funds_status: "NONCASH_ONLY",
        programs: [{ id: "p1", name: "Synthetic Grant Program", year: 2027,
          source: "PRIVATE", policy_version: "POLICY_2027_V1",
          applications: 1, eligible: 1, unreviewed: 0, noncash_committed_cents: 5000 }],
        totals: { programs: 1, applications: 1, noncash_committed_cents: 5000 } }));
});
afterEach(() => { cleanup(); vi.resetAllMocks(); });

describe("Standalone Jireh SGO read-only grantor UI", () => {
  it("shows noncash pilot data only and never selects a school tenant", async () => {
    render(<JirehSGODashboard />);
    expect(await screen.findByText("Synthetic Grant Program")).toBeTruthy();
    expect(screen.getAllByText(/\$50\.00/).length).toBeGreaterThan(0);
    expect(screen.getByText(/not funded, cleared, allocated, or paid/i)).toBeTruthy();
    expect(authenticatedFetch).toHaveBeenCalledTimes(2);
    for (const [url, opts] of authenticatedFetch.mock.calls) {
      expect(url).toMatch(/^\/api\/v1\/jireh-sgo\/organizations\//);
      expect(opts.omitSchoolContext).toBe(true);
      expect(opts.method).toBe("GET");
    }
  });
  it("fails closed without an authenticated session", () => {
    getAccessToken.mockReturnValue("");
    render(<JirehSGODashboard />);
    expect(screen.getByRole("alert").textContent).toMatch(/sign-in/i);
    expect(authenticatedFetch).not.toHaveBeenCalled();
  });
  it("immediately hides cached grantor data after logout", async () => {
    const view = render(<JirehSGODashboard />);
    expect(await screen.findByText("Synthetic Grant Program")).toBeTruthy();
    getAccessToken.mockReturnValue("");
    view.rerender(<JirehSGODashboard />);
    expect(screen.getByRole("alert").textContent).toMatch(/sign-in/i);
    expect(screen.queryByText("Synthetic Grant Program")).toBeNull();
    expect(screen.queryByLabelText("SGO membership")).toBeNull();
    expect(screen.queryByText("Noncash commitments:")).toBeNull();
  });

  it("does not show data from a mismatched organization", async () => {
    authenticatedFetch.mockImplementation(async (url) =>
      url.endsWith("/organizations/")
        ? response({ organizations: [{ id: "org-1", name: "Synthetic SGO", role: "VIEWER" }],
          funds_status: "NONCASH_ONLY" })
        : response({ organization: { id: "foreign", name: "Foreign" }, programs: [],
          funds_status: "NONCASH_ONLY" }));
    render(<JirehSGODashboard />);
    await waitFor(() => expect(screen.getByRole("alert").textContent).toMatch(/unavailable/i));
    expect(screen.queryByText("Foreign")).toBeNull();
  });
});
