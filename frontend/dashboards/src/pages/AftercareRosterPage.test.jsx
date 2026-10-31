// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CareHandoffDialog, CarePickupDialog } from "../components/care/CareCustodyDialogs.jsx";
import AftercareRosterPage from "./AftercareRosterPage.jsx";
import * as api from "../api/aftercareApi.js";

vi.mock("../api/aftercareApi.js", () => ({
  fetchRosterToday: vi.fn(),
  checkinStudent: vi.fn(),
  checkoutStudent: vi.fn(),
  fetchPickupContacts: vi.fn(),
  handoffToSchool: vi.fn(),
}));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <main>{children}</main>,
}));

const rows = [{
  student_id: "synthetic-child-1",
  student_name: "Synthetic Child",
  care_session: "AM",
  enrollment: { billing_model: "FLAT_MONTHLY" },
  attendance: null,
  unscheduled: false,
}];
beforeEach(() => {
  api.fetchRosterToday.mockResolvedValue({
    care_session: "AM", date: "2026-10-30", dow: "FRI", rows,
    unlinked_attendance_count: 0,
  });
  api.checkinStudent.mockResolvedValue({ id: 1 });
});
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

describe("care custody dialog safety and consistency", () => {
  it("requires direct receiving staff acknowledgement before allowing handoff", () => {
    const confirm = vi.fn();
    const acknowledge = vi.fn();
    const props = {
      open: true, studentName: "Synthetic Child", acknowledged: false, busy: false,
      onAcknowledge: acknowledge, onConfirm: confirm, onCancel: vi.fn(),
    };
    const view = render(<CareHandoffDialog {...props} />);
    const button = screen.getByRole("button", { name: "Record School Handoff" });
    expect(button.disabled).toBe(true);
    expect(screen.getByRole("dialog", { name: /Confirm School Handoff.*Synthetic Child/i })).toBeTruthy();
    fireEvent.click(screen.getByRole("checkbox"));
    expect(acknowledge).toHaveBeenCalledWith(true);
    view.rerender(<CareHandoffDialog {...props} acknowledged />);
    fireEvent.click(screen.getByRole("button", { name: "Record School Handoff" }));
    expect(confirm).toHaveBeenCalledTimes(1);
  });

  it("blocks pickup without an active contact and a current identity attestation", () => {
    const confirm = vi.fn();
    const props = {
      open: true, studentName: "Synthetic Child", contacts: [],
      selectedContactId: "", verified: false, busy: false,
      onSelectContact: vi.fn(), onVerify: vi.fn(), onConfirm: confirm, onCancel: vi.fn(),
    };
    const view = render(<CarePickupDialog {...props} />);
    expect(screen.getByRole("dialog", { name: /Verify Authorized Pickup.*Synthetic Child/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Confirm Checkout" }).disabled).toBe(true);
    expect(screen.getByText(/No active authorized pickup contacts/)).toBeTruthy();
    view.rerender(<CarePickupDialog {...props}
      contacts={[{ id: 7, name: "Authorized Guardian", is_active: true }]}
      selectedContactId="7" verified />);
    fireEvent.click(screen.getByRole("button", { name: "Confirm Checkout" }));
    expect(confirm).toHaveBeenCalledTimes(1);
  });

  it("reports check-in failure inline without a blocking browser alert", async () => {
    api.checkinStudent.mockRejectedValue(new Error("API authorization denied"));
    const alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
    render(<AftercareRosterPage careSession="AM" />);
    expect(await screen.findByText("Synthetic Child")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Check In" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toMatch(/Check-in failed.*authorization denied/));
    expect(alertSpy).not.toHaveBeenCalled();
    alertSpy.mockRestore();
  });

  it("blocks a repeated check-in submission while the first request is in flight", async () => {
    let finish;
    api.checkinStudent.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
    render(<AftercareRosterPage careSession="AM" />);
    await screen.findByText("Synthetic Child");
    fireEvent.click(screen.getByRole("button", { name: "Check In" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Checking In..." }).disabled).toBe(true));
    expect(api.checkinStudent).toHaveBeenCalledTimes(1);
    finish({ id: 1 });
    await waitFor(() => expect(api.fetchRosterToday).toHaveBeenCalledTimes(2));
  });
});
