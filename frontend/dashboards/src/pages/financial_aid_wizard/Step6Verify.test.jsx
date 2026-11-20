// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Step6Verify from "./Step6Verify.jsx";
import { verifyAidSetup } from "../../api/aid_wizard.js";

vi.mock("../../api/aid_wizard.js", () => ({
  verifyAidSetup: vi.fn(),
}));
vi.mock("../../components/crown/CrownWizardStepHeader.jsx", () => ({
  default: ({ title }) => <h2>{title}</h2>,
}));

const SESSION = "aid-session-1";

function renderStep(context = { sessionId: SESSION }) {
  const setContext = vi.fn();
  render(
    <Step6Verify
      context={context}
      setContext={setContext}
      stepIndex={5}
      totalSteps={6}
      steps={["Year", "Buckets", "Awards", "Preview", "Commit", "Verify"]}
    />,
  );
  return { setContext };
}

afterEach(() => cleanup());
beforeEach(() => vi.clearAllMocks());

describe("Financial Aid setup verification truth", () => {
  it("shows completion only for the matching verified session without errors", async () => {
    verifyAidSetup.mockResolvedValue({
      session_id: SESSION,
      status: "verified",
      awards_created: 2,
      awards_skipped: 0,
      errors: [],
    });
    const { setContext } = renderStep();

    expect((await screen.findByRole("status")).textContent).toContain("Financial aid setup complete! Status: verified");
    expect(screen.getByText("2")).toBeTruthy();
    expect(verifyAidSetup).toHaveBeenCalledWith(SESSION);
    expect(setContext).toHaveBeenCalledWith(expect.any(Function));
  });

  it("does not call verification or claim success for cached incomplete status", () => {
    renderStep({ sessionId: SESSION, verify: { session_id: SESSION, status: "committed", awards_created: 2, errors: [] } });

    expect(verifyAidSetup).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toContain("not verified");
    expect(screen.queryByText(/Financial aid setup complete!/)).toBeNull();
  });

  it.each([
    [{ session_id: SESSION, status: "unknown", errors: [] }, "unknown"],
    [{ session_id: SESSION, errors: [] }, "unknown"],
    [{ session_id: "another-session", status: "verified", errors: [] }, "verified"],
    [{ session_id: SESSION, status: "verified", errors: ["Rejected award"] }, "verified"],
    [{ session_id: SESSION, status: "verified", errors: "malformed" }, "verified"],
  ])("rejects incomplete or untrusted verification results %#", async (payload, status) => {
    verifyAidSetup.mockResolvedValue(payload);
    renderStep();

    expect((await screen.findByRole("alert")).textContent).toContain(`Financial aid setup is not verified. Status: ${status}.`);
    expect(screen.queryByText(/Financial aid setup complete!/)).toBeNull();
  });

  it("shows a rejected API response without claiming completion", async () => {
    verifyAidSetup.mockRejectedValue(new Error("Verification failed"));
    renderStep();

    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Verification failed"));
    expect(screen.queryByText(/Financial aid setup complete!/)).toBeNull();
  });
});
