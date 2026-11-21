// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import FinancialAidWizard from "./FinancialAidWizard.jsx";
import { AUTH_CONTEXT_CHANGE_EVENT, authenticatedJson, clearBrowserAuthState, setAccessToken, setSelectedSchoolId } from "../utils/authClient.js";
vi.mock("../utils/authClient.js", async (importOriginal) => ({
  ...(await importOriginal()),
  authenticatedJson: vi.fn(),
}));
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
const PREFIX = "crown_wizard_draft:financial-aid-setup";
const A_KEY = PREFIX + ":school-a:user-a";
const B_KEY = PREFIX + ":school-b:user-a";
const OTHER_USER_KEY = PREFIX + ":school-a:user-b";
function signIn(id, school = "school-a") {
  setAccessToken("synthetic-" + id);
  sessionStorage.setItem("crown_current_user", JSON.stringify({ id, school_id: school }));
  setSelectedSchoolId(school);
  window.dispatchEvent(new Event(AUTH_CONTEXT_CHANGE_EVENT));
}
beforeEach(() => { localStorage.clear(); sessionStorage.clear(); authenticatedJson.mockReset(); });
afterEach(() => { cleanup(); localStorage.clear(); sessionStorage.clear(); });
describe("Financial Aid wizard authenticated school and account isolation", () => {
  it("removes legacy local aid drafts but retains unrelated drafts", async () => {
    localStorage.setItem(PREFIX, "legacy");
    localStorage.setItem(PREFIX + ":school-a", "legacy school-only");
    localStorage.setItem("crown_wizard_draft:billing-setup", "preserve billing");
    signIn("user-a");
    render(<FinancialAidWizard />);
    expect((await screen.findByTestId("aid-cycle-session")).textContent).toBe("No saved aid cycle");
    await waitFor(() => expect(localStorage.getItem(PREFIX + ":school-a")).toBeNull());
    expect(localStorage.getItem(PREFIX)).toBeNull();
    expect(localStorage.getItem("crown_wizard_draft:billing-setup")).toBe("preserve billing");
  });
  it("restores a verified same-account draft without mixing schools", async () => {
    signIn("user-a");
    render(<FinancialAidWizard />);
    await screen.findByTestId("aid-cycle-session");
    fireEvent.click(screen.getByRole("button", { name: "Stage synthetic award" }));
    await waitFor(() => expect(sessionStorage.getItem(A_KEY)).toContain("school-a-cycle"));
    expect(localStorage.getItem(A_KEY)).toBeNull();
    // The original session identity belongs to school A. Switching to school B
    // must first be verified by the canonical authenticated whoami endpoint.
    authenticatedJson.mockResolvedValue({
      ok: true,
      user: { id: "user-a", school_id: "school-a" },
      tenant: { resolved_school_id: "school-b" },
    });
    setSelectedSchoolId("school-b");
    await waitFor(() => expect(authenticatedJson).toHaveBeenCalledWith("/api/system/whoami/"));
    await waitFor(() => expect(screen.getByTestId("aid-cycle-session").textContent).toBe("No saved aid cycle"));
    expect(sessionStorage.getItem(B_KEY)).not.toContain("school-a-cycle");
    setSelectedSchoolId("school-a");
    await waitFor(() => expect(screen.getByTestId("aid-cycle-session").textContent).toBe("school-a-cycle"));
  });
  it("does not expose one user's session draft to a second user at the same school", async () => {
    signIn("user-a");
    render(<FinancialAidWizard />);
    await screen.findByTestId("aid-cycle-session");
    fireEvent.click(screen.getByRole("button", { name: "Stage synthetic award" }));
    await waitFor(() => expect(sessionStorage.getItem(A_KEY)).toContain("school-a-cycle"));
    sessionStorage.setItem("crown.jwt.access", "synthetic-user-b");
    sessionStorage.setItem("crown_current_user", JSON.stringify({ id: "user-b" }));
    window.dispatchEvent(new Event(AUTH_CONTEXT_CHANGE_EVENT));
    await waitFor(() => expect(screen.getByTestId("aid-cycle-session").textContent).toBe("No saved aid cycle"));
    expect(sessionStorage.getItem(OTHER_USER_KEY) ?? "").not.toContain("school-a-cycle");
  });
  it("purges the financial aid draft on logout without clearing other wizard drafts", async () => {
    signIn("user-a");
    render(<FinancialAidWizard />);
    await screen.findByTestId("aid-cycle-session");
    fireEvent.click(screen.getByRole("button", { name: "Stage synthetic award" }));
    await waitFor(() => expect(sessionStorage.getItem(A_KEY)).toContain("school-a-cycle"));
    sessionStorage.setItem("crown_wizard_draft:billing-setup", "keep");
    clearBrowserAuthState();
    expect(sessionStorage.getItem(A_KEY)).toBeNull();
    expect(sessionStorage.getItem("crown_wizard_draft:billing-setup")).toBe("keep");
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Select a school"));
    signIn("user-b");
    await waitFor(() => expect(screen.getByTestId("aid-cycle-session").textContent).toBe("No saved aid cycle"));
  });
  it("loads a sandbox session only after verified server identity", async () => {
    setAccessToken("synthetic-sandbox-access");
    setSelectedSchoolId("school-a");
    authenticatedJson.mockResolvedValue({
      ok: true,
      user: { id: "sandbox-staff-1", school_id: "school-a" },
      tenant: { resolved_school_id: "school-a" },
    });
    render(<FinancialAidWizard />);
    expect((await screen.findByTestId("aid-cycle-session")).textContent).toBe("No saved aid cycle");
    expect(authenticatedJson).toHaveBeenCalledWith("/api/system/whoami/");
    expect(sessionStorage.getItem(PREFIX + ":school-a:sandbox-staff-1")).not.toContain("school-a-cycle");
  });
  it("fails closed if the sandbox identity is from another school", async () => {
    setAccessToken("synthetic-sandbox-access");
    setSelectedSchoolId("school-a");
    authenticatedJson.mockResolvedValue({
      ok: true,
      user: { id: "other-school-staff", school_id: "school-b" },
      tenant: { resolved_school_id: "school-b" },
    });
    render(<FinancialAidWizard />);
    await waitFor(() => expect(authenticatedJson).toHaveBeenCalledWith("/api/system/whoami/"));
    expect(screen.queryByTestId("aid-cycle-session")).toBeNull();
    expect(screen.getByRole("alert").textContent).toContain("verified school staff identity");
  });
  it("fails closed with no authenticated user", () => {
    setAccessToken("test-token"); setSelectedSchoolId("school-a");
    render(<FinancialAidWizard />);
    expect(screen.getByRole("alert").textContent).toContain("verified school staff identity");
  });
  it("fails closed with no school", () => {
    render(<FinancialAidWizard />);
    expect(screen.getByRole("alert").textContent).toContain("Select a school");
  });
});
