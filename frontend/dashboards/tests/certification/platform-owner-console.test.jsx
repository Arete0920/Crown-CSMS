import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import PlatformOwnerConsole from "../../src/pages/PlatformOwnerConsole.jsx";
import { authenticatedJson } from "../../src/utils/authClient.js";

vi.mock("../../src/utils/authClient.js", () => ({
  authenticatedJson: vi.fn(),
}));

const overview = {
  schools: { total: 120, by_status: { active: 120 } },
  provisioning: { by_state: { queued: 0 }, recent_jobs: [] },
  audit: { events_last_7_days: 0 },
  company_finance: { data_state: "not_configured", reason: "No corporate ledger configured." },
  external_payments: { provisioning_policy: "disabled" },
  meta: { data_source: "live_db", as_of: "2026-10-23T16:00:00Z" },
};

function schoolPage(page) {
  const count = page === 3 ? 20 : 50;
  return {
    total: 120,
    page,
    per_page: 50,
    results: Array.from({ length: count }, (_, index) => {
      const number = (page - 1) * 50 + index + 1;
      return {
        school_id: `synthetic-${number}`,
        school_name: `Synthetic School ${String(number).padStart(3, "0")}`,
        status: "active",
        plan_code: "starter",
        payment_provider: "none",
      };
    }),
  };
}

beforeEach(() => {
  vi.mocked(authenticatedJson).mockReset();
  vi.mocked(authenticatedJson).mockImplementation((endpoint, options) => {
    if (endpoint === "/api/platform/overview") return Promise.resolve(overview);
    if (endpoint === "/api/platform/schools/list") {
      return Promise.resolve(schoolPage(options.query.page));
    }
    return Promise.reject(new Error("Unexpected endpoint"));
  });
});

afterEach(() => cleanup());

describe("platform owner console verified behavior", () => {
  it("paginates all school records without a tenant header or write operation", async () => {
    render(<PlatformOwnerConsole />);
    expect(await screen.findByText("Page 1 of 3")).toBeTruthy();
    expect(screen.getByText("Synthetic School 001")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(await screen.findByText("Page 2 of 3")).toBeTruthy();
    expect(screen.getByText("Synthetic School 051")).toBeTruthy();
    expect(screen.queryByText("Synthetic School 001")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Next page" }));
    expect(await screen.findByText("Page 3 of 3")).toBeTruthy();
    expect(screen.getByText("Synthetic School 120")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Next page" }).disabled).toBe(true);

    const calls = vi.mocked(authenticatedJson).mock.calls;
    expect(calls.every(([, options]) => options.omitSchoolContext === true)).toBe(true);
    expect(calls.every(([, options]) => options.signal instanceof AbortSignal)).toBe(true);
    expect(calls.filter(([path]) => path === "/api/platform/schools/list")
      .map(([, options]) => options.query.page)).toEqual([1, 2, 3]);
  });

  it("withholds school directory content when the server denies operator access", async () => {
    vi.mocked(authenticatedJson).mockImplementation((endpoint) => endpoint === "/api/platform/overview"
      ? Promise.reject(Object.assign(new Error("Unauthorized"), { status: 403 }))
      : Promise.resolve(schoolPage(1)));
    render(<PlatformOwnerConsole />);
    expect(await screen.findByText(/Access denied: active platform-operator/)).toBeTruthy();
    expect(screen.queryByRole("table", { name: "Platform school directory" })).toBeNull();
  });

  it("cancels in-flight read-only requests when unmounted", async () => {
    let signal;
    vi.mocked(authenticatedJson).mockImplementation((_endpoint, options) => {
      signal = options.signal;
      return new Promise(() => {});
    });
    const view = render(<PlatformOwnerConsole />);
    await waitFor(() => expect(signal).toBeDefined());
    view.unmount();
    expect(signal.aborted).toBe(true);
  });
});
