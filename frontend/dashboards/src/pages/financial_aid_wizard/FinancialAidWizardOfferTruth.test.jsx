// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import Step4Preview from "./Step4Preview.jsx";
import Step5Commit from "./Step5Commit.jsx";

const steps = ["Year", "Buckets", "Awards", "Preview", "Commit", "Verify"];
const context = {
  sessionId: "wizard-session-1",
  aidYear: "2026-2027",
  buckets: ["need"],
  awards: [{ application_id: "7", student_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", bucket: "need", amount: "125.00", rationale: "" }],
};

afterEach(() => cleanup());

describe("Financial Aid wizard preview and commit language", () => {
  it("does not claim that staging zero offers records disbursements", () => {
    render(
      <Step4Preview
        context={{ ...context, awards: [] }}
        goNext={() => {}}
        goPrev={() => {}}
        stepIndex={3}
        totalSteps={6}
        steps={steps}
      />,
    );

    expect(screen.getByText(/No awards staged/i).textContent).toContain("No offered awards will be created");
    expect(screen.queryByText(/disbursement/i)).toBeNull();
  });

  it("identifies preview totals as staged offer amounts, not final aid awards", () => {
    render(
      <Step4Preview
        context={context}
        goNext={() => {}}
        goPrev={() => {}}
        stepIndex={3}
        totalSteps={6}
        steps={steps}
      />,
    );

    expect(screen.getByText("Total Staged Offer Amount")).toBeTruthy();
    expect(screen.getAllByText("$125.00")).toHaveLength(2);
    expect(screen.queryByText("Total Aid Amount")).toBeNull();
  });

  it("describes the possible skip of existing offers before commit", () => {
    render(
      <Step5Commit
        context={context}
        setContext={() => {}}
        goNext={() => {}}
        goPrev={() => {}}
        stepIndex={4}
        totalSteps={6}
        steps={steps}
      />,
    );

    expect(screen.getByText("Staged Awards")).toBeTruthy();
    expect(screen.getByText("Total Staged Offer Amount")).toBeTruthy();
    expect(screen.getByText(/Existing active offers are skipped/i)).toBeTruthy();
    expect(screen.getByText(/No payments or disbursements are made by this action/i)).toBeTruthy();
    expect(screen.queryByText("Awards to Create")).toBeNull();
  });
});
