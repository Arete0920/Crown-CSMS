import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiJson } from "../lib/api.js";
import { setAccessToken, setSelectedSchoolId } from "../utils/authClient.js";
import JirehAidDecisionsPage from "./JirehAidDecisionsPage.jsx";

vi.mock("../lib/api.js", () => ({ apiJson: vi.fn() }));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <main>{children}</main>,
}));

const SCHOOL = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const YEAR = "11111111-1111-4111-8111-111111111111";
const STUDENT = "22222222-2222-4222-8222-222222222222";
const SUMMARY = "/api/v1/dashboards/financial-aid/summary";
const OVERVIEW = "/api/aid/admin/overview/?academic_year_id=" + YEAR;
const REVIEW = "/api/aid/admin/applications/7/review/";
const RECOMMEND = "/api/aid/admin/recommend-award/";
const APPROVE = "/api/aid/admin/awards/41/approve/";
const application = { id: 7, school_id: SCHOOL, academic_year_id: YEAR,
  status: "SUBMITTED", household_size: 3 };
const award = { id: 41, school_id: SCHOOL, academic_year_id: YEAR,
  aid_application_id: 7, student_id: STUDENT, award_type: "NEED",
  decision_status: "OFFERED", ledger_entry_id: null, awarded_cents: 80000 };
const aidOverview = (awards) => ({ applications: [application], awards, budgets: [] });
const summary = (accepted = false) => ({ dashboard_key: "financial-aid", meta: {
  served_from: "live_db", school_id: SCHOOL, academic_year_id: YEAR,
  accepted_award_face_value_cents: accepted ? 80000 : 0,
} });
const caseReview = { application_id: 7, students: [{ id: STUDENT,
  first_name: "Fictional", last_name: "Student", student_number: "F001" }],
  review_signals: [], financial_profile: { verification_status: "VERIFIED" } };

let offers, postCount, failOverview, originalWriteCommits, approved;

beforeEach(() => {
  vi.resetAllMocks();
  sessionStorage.clear(); localStorage.clear();
  setAccessToken("synthetic-officer"); setSelectedSchoolId(SCHOOL);
  offers = []; postCount = 0; failOverview = false;
  originalWriteCommits = true; approved = false;
  apiJson.mockImplementation(async (path, options) => {
    if (path === SUMMARY) return summary(approved);
    if (path === OVERVIEW) {
      if (failOverview) throw new Error("GET temporarily unavailable");
      return aidOverview(offers.map((item) => approved
        ? { ...item, decision_status: "ACCEPTED", ledger_entry_id: "ledger-1" } : item));
    }
    if (path === REVIEW) return caseReview;
    if (path === RECOMMEND && options?.method === "POST") {
      postCount++;
      if (originalWriteCommits) offers = [award];
      throw new Error("response lost after POST");
    }
    if (path === APPROVE && options?.method === "POST") {
      postCount++; approved = true;
      throw new Error("response lost after approval POST");
    }
    throw new Error("Unexpected request: " + path);
  });
});
afterEach(() => { cleanup(); sessionStorage.clear(); localStorage.clear(); });

async function selectReviewedCase() {
  fireEvent.click(await screen.findByRole("button", { name: /Application #7/ }));
  const checkbox = await screen.findByRole("checkbox");
  fireEvent.click(checkbox);
}

async function attemptOffer() {
  await selectReviewedCase();
  fireEvent.change(screen.getByPlaceholderText("e.g. 12500.00"),
    { target: { value: "12500.00" } });
  fireEvent.click(screen.getByRole("button", { name: /Calculate and save an OFFERED award/ }));
  await waitFor(() => expect(postCount).toBe(1));
  await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("reconciliation"));
}

describe("Jireh ambiguous award write reconciliation", () => {
  it("does not repeat an offered award after a committed POST and failed refresh", async () => {
    render(<JirehAidDecisionsPage />);
    await attemptOffer();
    const submit = screen.getByRole("button", { name: /Calculate and save an OFFERED award/ });
    expect(submit.disabled).toBe(true);

    failOverview = true;
    fireEvent.click(screen.getByRole("button", { name: "Refresh and reconcile records" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("prior write"));
    expect(submit.disabled).toBe(true);
    fireEvent.click(submit);
    expect(postCount).toBe(1);

    failOverview = false;
    fireEvent.click(screen.getByRole("button", { name: "Refresh and reconcile records" }));
    await screen.findByText(/independently reconciled; no second request submitted/);
    expect(postCount).toBe(1);
    // The saved offer itself remains a duplicate barrier after reconciliation.
    expect(submit.disabled).toBe(true);
  });

  it("keeps writes disabled when the original POST cannot be confirmed", async () => {
    originalWriteCommits = false;
    render(<JirehAidDecisionsPage />);
    await attemptOffer();
    fireEvent.click(screen.getByRole("button", { name: "Refresh and reconcile records" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent)
      .toContain("No committed matching offer was verified"));
    const submit = screen.getByRole("button", { name: /Calculate and save an OFFERED award/ });
    expect(submit.disabled).toBe(true);
    fireEvent.click(submit);
    expect(postCount).toBe(1);
  });

  it("reconciles a committed approval and ledger without a second approval POST", async () => {
    offers = [award];
    render(<JirehAidDecisionsPage />);
    await selectReviewedCase();
    fireEvent.change(screen.getByRole("textbox", { name: /Type APPROVE/ }),
      { target: { value: "APPROVE" } });
    fireEvent.click(screen.getByRole("button", { name: /Approve and verify ledger/ }));
    await waitFor(() => expect(postCount).toBe(1));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Do not retry"));

    failOverview = true;
    fireEvent.click(screen.getByRole("button", { name: "Refresh and reconcile records" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("prior write"));
    expect(postCount).toBe(1);

    failOverview = false;
    fireEvent.click(screen.getByRole("button", { name: "Refresh and reconcile records" }));
    await screen.findByText(/ledger credit independently reconciled/);
    expect(postCount).toBe(1);
  });
});
