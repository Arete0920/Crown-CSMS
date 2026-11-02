// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import SummerCampSetupWizard from "./SummerCampSetupWizard.jsx";
import { fetchSummerCampWizard, submitSummerCampWizard } from "../../api/summerCampApi.js";

vi.mock("../../api/summerCampApi.js", () => ({
  fetchSummerCampWizard: vi.fn(), submitSummerCampWizard: vi.fn(),
}));
vi.mock("../../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <main>{children}</main>,
}));
vi.mock("../../components/layout/DashboardSection.jsx", () => ({
  default: ({ children }) => <section>{children}</section>,
}));
const config = { camp_name: "Synthetic Camp", default_capacity: 20,
  default_staff_ratio: 8, public_registration_enabled: false, billing_policy: "PER_SESSION" };
const response = () => ({ config: { ...config },
  wizard: { completed_steps: ["Program"], is_completed: false } });
beforeEach(() => {
  vi.resetAllMocks();
  fetchSummerCampWizard.mockResolvedValue(response());
  submitSummerCampWizard.mockResolvedValue({ status: "ok" });
});
afterEach(cleanup);

it("withholds editing when the initial read fails", async () => {
  fetchSummerCampWizard.mockRejectedValue(new Error("Unavailable"));
  render(<SummerCampSetupWizard />);
  await screen.findByRole("alert");
  expect(screen.queryByRole("button", { name: "Save Setup" })).toBeNull();
  expect(submitSummerCampWizard).not.toHaveBeenCalled();
});
it("verifies a save using a separate GET and clears success after an edit", async () => {
  render(<SummerCampSetupWizard />);
  fireEvent.click(await screen.findByRole("button", { name: "Save Setup" }));
  await screen.findByText(/Saved and verified against server records/);
  expect(fetchSummerCampWizard).toHaveBeenCalledTimes(2);
  expect(submitSummerCampWizard).toHaveBeenCalledWith({
    config, completed_steps: ["Program"], is_completed: false,
  });
  fireEvent.change(screen.getByLabelText("Camp Name"), { target: { value: "Changed" } });
  expect(screen.queryByText(/Saved and verified against server records/)).toBeNull();
});
it.each(["mismatch", "unavailable"])("does not claim success for %s readback", async (kind) => {
  fetchSummerCampWizard.mockResolvedValueOnce(response());
  if (kind === "mismatch") fetchSummerCampWizard.mockResolvedValue({
    ...response(), config: { ...config, default_capacity: 99 },
  });
  else fetchSummerCampWizard.mockRejectedValue(new Error("Readback unavailable"));
  render(<SummerCampSetupWizard />);
  fireEvent.click(await screen.findByRole("button", { name: "Save Setup" }));
  await screen.findByRole("alert");
  expect(screen.queryByText(/Saved and verified against server records/)).toBeNull();
  expect(screen.queryByRole("button", { name: "Save Setup" })).toBeNull();
  expect(submitSummerCampWizard).toHaveBeenCalledTimes(1);
});
it("freezes editing while save readback is pending", async () => {
  fetchSummerCampWizard.mockResolvedValueOnce(response()).mockImplementation(() => new Promise(() => {}));
  render(<SummerCampSetupWizard />);
  fireEvent.click(await screen.findByRole("button", { name: "Save Setup" }));
  await waitFor(() => expect(fetchSummerCampWizard).toHaveBeenCalledTimes(2));
  expect(screen.getByRole("group", { name: "Camp configuration" }).disabled).toBe(true);
});
