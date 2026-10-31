// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import SummerCampDashboard from "./SummerCampDashboard.jsx";
import { fetchSummerCampBoardSummary } from "../api/summerCampApi.js";

vi.mock("../api/summerCampApi.js", () => ({
  fetchSummerCampBoardSummary: vi.fn(),
}));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <div>{children}</div>,
}));
vi.mock("../components/layout/DashboardSection.jsx", () => ({
  default: ({ title, children }) => <section><h2>{title}</h2>{children}</section>,
}));

const baseSummary = {
  as_of: "2026-10-31",
  registered_campers: 4,
  sessions: 2,
  waitlist_count: 1,
  missing_forms: 0,
  health_review_count: 0,
  outstanding_balances: 2,
  incidents_mtd: 0,
  gross_revenue_cents: 12500,
};

beforeEach(() => {
  vi.mocked(fetchSummerCampBoardSummary).mockResolvedValue(baseSummary);
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Summer Camp board finance truth", () => {
  it("labels ledger-linked charges as obligations, not collected revenue", async () => {
    render(<SummerCampDashboard />);
    expect(await screen.findByText("$125.00")).toBeTruthy();
    expect(screen.getByText("Ledger-linked charges (not collected)")).toBeTruthy();
    expect(screen.getByText("Enrollments with balance due")).toBeTruthy();
    expect(screen.getByText(/not payment or settlement totals/)).toBeTruthy();
    expect(screen.queryByText("Gross Revenue")).toBeNull();
  });

  it.each([null, undefined, -1, "12500", 12.5])(
    "does not convert missing or invalid charges (%s) into zero cash",
    async (amount) => {
      vi.mocked(fetchSummerCampBoardSummary).mockResolvedValue({
        ...baseSummary,
        gross_revenue_cents: amount,
      });
      render(<SummerCampDashboard />);
      expect(await screen.findByText("Not available")).toBeTruthy();
      expect(screen.queryByText("$0.00")).toBeNull();
    },
  );

  it("displays an explicit zero only when the API actually returns zero linked charges", async () => {
    vi.mocked(fetchSummerCampBoardSummary).mockResolvedValue({
      ...baseSummary, gross_revenue_cents: 0,
    });
    render(<SummerCampDashboard />);
    expect(await screen.findByText("$0.00")).toBeTruthy();
    expect(screen.getByText("Ledger-linked charges (not collected)")).toBeTruthy();
  });
});
