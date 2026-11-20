// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Step1Year from "./Step1Year.jsx";
import Step2Buckets from "./Step2Buckets.jsx";
import {
  createAidWizardSession,
  configureAidWizardSession,
  saveAidBuckets,
} from "../../api/aid_wizard.js";

vi.mock("../../api/aid_wizard.js", () => ({
  createAidWizardSession: vi.fn(),
  configureAidWizardSession: vi.fn(),
  saveAidBuckets: vi.fn(),
}));
vi.mock("../../components/crown/CrownWizardStepHeader.jsx", () => ({
  default: ({ title }) => <h2>{title}</h2>,
}));

const SESSION = "wizard-session-1";
const STEPS = ["Aid Year", "Buckets", "Awards", "Preview", "Commit", "Verify"];

function transportError(status, statusText, data) {
  const error = new Error(`HTTP ${status} ${statusText}`);
  error.status = status;
  error.body = JSON.stringify(data);
  error.response = { status, statusText, data, headers: {} };
  return error;
}

function renderYear(context = { sessionId: SESSION }) {
  const goNext = vi.fn();
  render(
    <Step1Year
      context={context}
      setContext={vi.fn()}
      goNext={goNext}
      stepIndex={0}
      totalSteps={6}
      steps={STEPS}
    />,
  );
  fireEvent.change(screen.getByPlaceholderText("e.g. 2026-2027"), {
    target: { value: "2026-2027" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  return { goNext };
}

function renderBuckets() {
  const goNext = vi.fn();
  render(
    <Step2Buckets
      context={{ sessionId: SESSION, buckets: ["need"] }}
      setContext={vi.fn()}
      goNext={goNext}
      goPrev={vi.fn()}
      stepIndex={1}
      totalSteps={6}
      steps={STEPS}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Continue" }));
  return { goNext };
}

afterEach(() => cleanup());
beforeEach(() => vi.clearAllMocks());

describe("Financial Aid wizard server error messages", () => {
  it("shows the configured aid-year conflict from the parsed API response", async () => {
    configureAidWizardSession.mockRejectedValue(
      transportError(409, "Conflict", { error: "Finalized wizard sessions cannot be reconfigured" }),
    );
    const { goNext } = renderYear();

    expect(await screen.findByText("Finalized wizard sessions cannot be reconfigured")).toBeTruthy();
    expect(configureAidWizardSession).toHaveBeenCalledWith(SESSION, "2026-2027");
    expect(goNext).not.toHaveBeenCalled();
  });

  it("shows the permission detail when creating an aid-year session is denied", async () => {
    createAidWizardSession.mockRejectedValue(
      transportError(403, "Forbidden", { detail: "You do not have permission to configure Financial Aid." }),
    );
    const { goNext } = renderYear({});

    expect(await screen.findByText("You do not have permission to configure Financial Aid.")).toBeTruthy();
    expect(configureAidWizardSession).not.toHaveBeenCalled();
    expect(goNext).not.toHaveBeenCalled();
  });

  it("shows the bucket validation errors returned by the API", async () => {
    saveAidBuckets.mockRejectedValue(
      transportError(400, "Bad Request", { errors: [
        "buckets[0]: 'invalid' is not a valid bucket",
        "buckets[1]: 'unknown' is not a valid bucket",
      ] }),
    );
    const { goNext } = renderBuckets();

    expect(await screen.findByText("buckets[0]: 'invalid' is not a valid bucket; buckets[1]: 'unknown' is not a valid bucket")).toBeTruthy();
    expect(goNext).not.toHaveBeenCalled();
  });

  it("shows the bucket state conflict instead of an HTTP status code", async () => {
    saveAidBuckets.mockRejectedValue(
      transportError(409, "Conflict", { error: "Cannot save buckets from status 'awards_staged'" }),
    );
    const { goNext } = renderBuckets();

    expect(await screen.findByText("Cannot save buckets from status 'awards_staged'")).toBeTruthy();
    expect(goNext).not.toHaveBeenCalled();
  });

  it("retains transport error fallback when the API has no parsed message", async () => {
    saveAidBuckets.mockRejectedValue(new Error("Network request timed out"));
    const { goNext } = renderBuckets();

    expect(await screen.findByText("Network request timed out")).toBeTruthy();
    expect(goNext).not.toHaveBeenCalled();
  });
});
