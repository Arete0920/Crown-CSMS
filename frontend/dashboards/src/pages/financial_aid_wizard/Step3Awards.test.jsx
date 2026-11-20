// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Step3Awards from "./Step3Awards.jsx";
import { stageAidAwards } from "../../api/aid_wizard.js";

vi.mock("../../api/aid_wizard.js", () => ({ stageAidAwards: vi.fn() }));
vi.mock("../../components/crown/CrownWizardStepHeader.jsx", () => ({
  default: ({ title }) => <h2>{title}</h2>,
}));

const STUDENT = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const SESSION = "wizard-session-1";

function renderStep(awards) {
  const setContext = vi.fn();
  const goNext = vi.fn();
  render(
    <Step3Awards
      context={{ sessionId: SESSION, buckets: ["need"], ...(awards ? { awards } : {}) }}
      setContext={setContext}
      goNext={goNext}
      goPrev={vi.fn()}
      stepIndex={2}
      totalSteps={6}
      steps={["Year", "Buckets", "Awards", "Preview", "Commit", "Verify"]}
    />,
  );
  return { setContext, goNext };
}

function completeFirstRow() {
  fireEvent.change(screen.getAllByPlaceholderText("Canonical Jireh application ID")[0], { target: { value: "7" } });
  fireEvent.change(screen.getAllByPlaceholderText("UUID of the student receiving this award")[0], { target: { value: STUDENT } });
  fireEvent.change(screen.getAllByPlaceholderText("0.00")[0], { target: { value: "250.00" } });
}

afterEach(() => cleanup());
beforeEach(() => {
  vi.clearAllMocks();
  stageAidAwards.mockResolvedValue({ status: "awards_staged", awards_count: 1 });
});

describe("Financial Aid staging rows", () => {
  it("blocks a partially entered row rather than silently dropping it", () => {
    const { goNext } = renderStep();
    completeFirstRow();
    fireEvent.click(screen.getByRole("button", { name: "+ Add Award" }));
    fireEvent.change(screen.getAllByPlaceholderText("Canonical Jireh application ID")[1], { target: { value: "8" } });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByRole("alert").textContent).toContain("Award #2:");
    expect(stageAidAwards).not.toHaveBeenCalled();
    expect(goNext).not.toHaveBeenCalled();
  });

  it("permits a blank extra row without generating an unintended award", async () => {
    const { setContext, goNext } = renderStep();
    completeFirstRow();
    fireEvent.click(screen.getByRole("button", { name: "+ Add Award" }));
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    await waitFor(() => expect(goNext).toHaveBeenCalledTimes(1));
    expect(stageAidAwards).toHaveBeenCalledWith(SESSION, [{
      application_id: "7", student_id: STUDENT, bucket: "need", amount: "250.00", rationale: "",
    }]);
    expect(setContext).toHaveBeenCalledWith(expect.any(Function));
  });

  it("does not silently stage a student without an application ID", () => {
    renderStep();
    fireEvent.change(screen.getByPlaceholderText("UUID of the student receiving this award"), { target: { value: STUDENT } });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByRole("alert").textContent).toContain("Award #1:");
    expect(stageAidAwards).not.toHaveBeenCalled();
  });

  it("does not silently stage an award with a missing amount", () => {
    renderStep();
    fireEvent.change(screen.getByPlaceholderText("Canonical Jireh application ID"), { target: { value: "7" } });
    fireEvent.change(screen.getByPlaceholderText("UUID of the student receiving this award"), { target: { value: STUDENT } });
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByRole("alert").textContent).toContain("amount are required");
    expect(stageAidAwards).not.toHaveBeenCalled();
  });

  it("retains the explicit no-awards skip path", async () => {
    const { goNext } = renderStep();
    fireEvent.click(screen.getByRole("button", { name: /No Awards/ }));
    await waitFor(() => expect(goNext).toHaveBeenCalledTimes(1));
    expect(stageAidAwards).toHaveBeenCalledWith(SESSION, []);
  });

  it("preserves backend errors without advancing the wizard", async () => {
    stageAidAwards.mockRejectedValue(new Error("Award amount rejected"));
    const { goNext } = renderStep();
    completeFirstRow();
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Award amount rejected"));
    expect(goNext).not.toHaveBeenCalled();
  });
});
