// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import FinanceSetupWizard from "./FinanceSetupWizard.jsx";

const fetchFinanceStatusMock = vi.fn();
const saveFinancePolicyMock = vi.fn();
const lockFinancePolicyMock = vi.fn();

vi.mock("../../api/financeSetupApi.js", () => ({
  fetchFinanceStatus: (...args) => fetchFinanceStatusMock(...args),
  saveFinancePolicy: (...args) => saveFinancePolicyMock(...args),
  lockFinancePolicy: (...args) => lockFinancePolicyMock(...args),
}));

function getRowSpinbutton(label) {
  const labelNode = screen.getByText(label);
  const row = labelNode.parentElement?.parentElement;
  if (!row) {
    throw new Error(`Unable to find row for label: ${label}`);
  }
  return within(row).getByRole("spinbutton");
}

async function openReviewStep() {
  await waitFor(() => {
    expect(fetchFinanceStatusMock).toHaveBeenCalledTimes(1);
  });
  fireEvent.click(screen.getByRole("button", { name: /Review & Lock/i }));
}

beforeEach(() => {
  fetchFinanceStatusMock.mockResolvedValue(null);
  saveFinancePolicyMock.mockResolvedValue({ data: { version: { is_locked: false } } });
  lockFinancePolicyMock.mockResolvedValue({ locked_at: "now" });
  vi.spyOn(window, "confirm").mockReturnValue(true);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  fetchFinanceStatusMock.mockReset();
  saveFinancePolicyMock.mockReset();
  lockFinancePolicyMock.mockReset();
});

describe("FinanceSetupWizard numeric validation", () => {
  it("rejects negative max_discount_percent_bp", async () => {
    render(<FinanceSetupWizard />);

    fireEvent.click(await screen.findByRole("button", { name: /Discounts/i }));
    fireEvent.change(getRowSpinbutton("Max combined discount (bp)"), { target: { value: "-1" } });

    await openReviewStep();
    fireEvent.click(screen.getByRole("button", { name: /Save Draft/i }));

    expect(saveFinancePolicyMock).not.toHaveBeenCalled();
    expect(screen.getByText("Max combined discount must be between 0 and 10000 basis points.")).toBeTruthy();
  });

  it("rejects max_discount_percent_bp above 10000", async () => {
    render(<FinanceSetupWizard />);

    fireEvent.click(await screen.findByRole("button", { name: /Discounts/i }));
    fireEvent.change(getRowSpinbutton("Max combined discount (bp)"), { target: { value: "10001" } });

    await openReviewStep();
    fireEvent.click(screen.getByRole("button", { name: /Save Draft/i }));

    expect(saveFinancePolicyMock).not.toHaveBeenCalled();
    expect(screen.getByText("Max combined discount must be between 0 and 10000 basis points.")).toBeTruthy();
  });

  it("accepts valid max_discount_percent_bp", async () => {
    render(<FinanceSetupWizard />);

    fireEvent.click(await screen.findByRole("button", { name: /Discounts/i }));
    fireEvent.change(getRowSpinbutton("Max combined discount (bp)"), { target: { value: "5000" } });

    await openReviewStep();
    fireEvent.click(screen.getByRole("button", { name: /Save Draft/i }));

    await waitFor(() => {
      expect(saveFinancePolicyMock).toHaveBeenCalledTimes(1);
    });
  });

  it("rejects negative application_fee_cents", async () => {
    render(<FinanceSetupWizard />);

    fireEvent.click(await screen.findByRole("button", { name: /Aid/i }));
    fireEvent.change(getRowSpinbutton("Application fee"), { target: { value: "-1" } });

    await openReviewStep();
    fireEvent.click(screen.getByRole("button", { name: /Save Draft/i }));

    expect(saveFinancePolicyMock).not.toHaveBeenCalled();
    expect(screen.getByText("Application fee must be 0 or greater.")).toBeTruthy();
  });
});
