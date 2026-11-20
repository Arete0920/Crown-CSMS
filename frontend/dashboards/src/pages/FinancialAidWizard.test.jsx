// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import FinancialAidWizard from "./FinancialAidWizard.jsx";
import { setSelectedSchoolId } from "../utils/authClient.js";

vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <div>{children}</div>,
}));
vi.mock("./financial_aid_wizard/Step1Year.jsx", () => ({
  default: ({ context, setContext }) => (
    <div>
      <output data-testid="aid-cycle-session">{context.sessionId || "No saved aid cycle"}</output>
      <button type="button" onClick={() => setContext({
        sessionId: "school-a-cycle",
        awards: [{ student_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", amount: "125.00" }],
      })}>Stage synthetic award</button>
    </div>
  ),
}));

const LEGACY_KEY = "crown_wizard_draft:financial-aid-setup";
const SCHOOL_A_KEY = "crown_wizard_draft:financial-aid-setup:school-a";
const SCHOOL_B_KEY = "crown_wizard_draft:financial-aid-setup:school-b";

beforeEach(() => {
  window.localStorage.clear();
  window.sessionStorage.clear();
});
afterEach(() => {
  cleanup();
  window.localStorage.clear();
  window.sessionStorage.clear();
});

describe("Financial Aid wizard client-side school isolation", () => {
  it("does not render or retain a legacy unscoped financial aid draft", async () => {
    window.localStorage.setItem(LEGACY_KEY, JSON.stringify({
      __draftVersion: 2,
      value: { sessionId: "old-school-cycle", awards: [{ student_id: "old-student" }] },
      savedAt: "2026-11-20T00:00:00.000Z",
    }));
    setSelectedSchoolId("school-b");
    render(<FinancialAidWizard />);

    expect((await screen.findByTestId("aid-cycle-session")).textContent).toBe("No saved aid cycle");
    await waitFor(() => expect(window.localStorage.getItem(LEGACY_KEY)).toBeNull());
    expect(screen.queryByText("old-school-cycle")).toBeNull();
  });

  it("remounts with the selected school's draft when changing schools in the same tab", async () => {
    setSelectedSchoolId("school-a");
    render(<FinancialAidWizard />);

    expect((await screen.findByTestId("aid-cycle-session")).textContent).toBe("No saved aid cycle");
    fireEvent.click(screen.getByRole("button", { name: "Stage synthetic award" }));
    expect(screen.getByTestId("aid-cycle-session").textContent).toBe("school-a-cycle");
    await waitFor(() => expect(
      JSON.parse(window.localStorage.getItem(SCHOOL_A_KEY)).value.awards[0].student_id,
    ).toBe("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"));

    setSelectedSchoolId("school-b");
    await waitFor(() => expect(screen.getByTestId("aid-cycle-session").textContent).toBe("No saved aid cycle"));
    expect(window.localStorage.getItem(SCHOOL_B_KEY)).not.toContain("school-a-cycle");
    expect(screen.queryByText("school-a-cycle")).toBeNull();

    setSelectedSchoolId("school-a");
    await waitFor(() => expect(screen.getByTestId("aid-cycle-session").textContent).toBe("school-a-cycle"));
  });

  it("does not mount school-owned saved Financial Aid content without a selected school", async () => {
    window.localStorage.setItem(LEGACY_KEY, JSON.stringify({
      __draftVersion: 2,
      value: { sessionId: "unscoped-cycle" },
    }));
    render(<FinancialAidWizard />);

    expect(screen.getByRole("alert").textContent).toContain("Select a school");
    expect(screen.queryByTestId("aid-cycle-session")).toBeNull();
    await waitFor(() => expect(window.localStorage.getItem(LEGACY_KEY)).toBeNull());
  });
});
