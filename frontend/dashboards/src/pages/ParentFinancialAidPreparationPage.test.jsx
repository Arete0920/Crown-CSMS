// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiFetch } from "../lib/api";
import ParentFinancialAidPreparationPage from "./ParentFinancialAidPreparationPage.jsx";

vi.mock("../lib/api", () => ({ apiFetch: vi.fn() }));
vi.mock("../features/parentJourney/ParentJourneyOverviewPage.jsx", () => ({
  default: () => null,
}));

const YEAR = "11111111-1111-4111-8111-111111111111";
const STUDENT = "22222222-2222-4222-8222-222222222222";
const APPLICATION = "33333333-3333-4333-8333-333333333333";

function snapshot(applications = []) {
  return {
    demo_only: true,
    household_name: "Fictional Family",
    academic_years: [{ id: YEAR, name: "2026-2027" }],
    students: [{ id: STUDENT, name: "Sample Learner" }],
    scenarios: [{ id: "fictional_modest", label: "Invented resources" }],
    applications,
  };
}

const saved = {
  id: APPLICATION,
  academic_year_id: YEAR,
  academic_year_name: "2026-2027",
  status: "SUBMITTED",
  submitted_at: "2026-11-02T15:00:00Z",
  student_ids: [STUDENT],
  awards: [],
};

function jsonResponse(payload) {
  return { json: async () => payload };
}

function arrange(readback) {
  let reads = 0;
  apiFetch.mockImplementation(async (_path, options = {}) => {
    if (options.method === "POST") {
      return jsonResponse({ demo_only: true, application: saved });
    }
    reads += 1;
    return jsonResponse(reads === 1 ? snapshot() : readback);
  });
}

async function submitFictionalApplication() {
  render(<ParentFinancialAidPreparationPage />);
  const submit = await screen.findByRole("button", {
    name: "Submit fictional Financial Aid application",
  });
  await waitFor(() => expect(submit.disabled).toBe(true));
  fireEvent.click(screen.getByRole("checkbox", {
    name: /I confirm all application information is fictional/i,
  }));
  expect(submit.disabled).toBe(false);
  fireEvent.click(submit);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubEnv("VITE_LOCAL_DEMO", "1");
});
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

describe("Fictional parent Financial Aid saved-record truth", () => {
  it("does not expose local fictional intake outside the explicit local demo build", () => {
    vi.stubEnv("VITE_LOCAL_DEMO", "0");
    render(<ParentFinancialAidPreparationPage />);
    expect(screen.queryByTestId("jireh-family-demo")).toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("confirms submission only after matching canonical authenticated GET readback", async () => {
    arrange(snapshot([saved]));
    await submitFictionalApplication();
    const message = await screen.findByTestId("jireh-submit-confirmation");
    expect(message.textContent).toContain(APPLICATION);
    expect(message.textContent).toContain("independently verified");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(apiFetch.mock.calls.map(([, options]) => options?.method || "GET")).toEqual([
      "GET", "POST", "GET",
    ]);
  });

  it("does not claim success when the server GET is missing the submitted application", async () => {
    arrange(snapshot());
    await submitFictionalApplication();
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "independent saved-record verification failed",
      );
    });
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
  });

  it("does not claim success when a submitted application is still a draft on GET", async () => {
    arrange(snapshot([{ ...saved, status: "DRAFT" }]));
    await submitFictionalApplication();
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "independent saved-record verification failed",
      );
    });
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
  });

  it("does not claim success when the readback has a foreign student reference", async () => {
    arrange(snapshot([{ ...saved, student_ids: ["44444444-4444-4444-8444-444444444444"] }]));
    await submitFictionalApplication();
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "independent saved-record verification failed",
      );
    });
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
  });
});
