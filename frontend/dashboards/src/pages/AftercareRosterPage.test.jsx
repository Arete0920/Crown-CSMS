// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { CareHandoffDialog, CarePickupDialog } from "../components/care/CareCustodyDialogs.jsx";
import AftercareRosterPage from "./AftercareRosterPage.jsx";
import * as api from "../api/aftercareApi.js";
import { getAccessToken, setAccessToken, setSelectedSchoolId } from "../utils/authClient.js";

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
  sessionStorage.setItem("crown.school.id", "fictional-care-school");
  setAccessToken("fictional-care-staff-access");
  api.fetchRosterToday.mockResolvedValue({
    care_session: "AM", date: "2026-10-30", dow: "FRI", rows,
    unlinked_attendance_count: 0,
  });
  api.checkinStudent.mockResolvedValue({ id: 1 });
});
afterEach(() => {
  cleanup();
  sessionStorage.clear();
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

describe("care roster tenant and staff-session isolation", () => {
  it("immediately hides previous staff children after same-school credential change", async () => {
    render(<AftercareRosterPage careSession="AM" />);
    expect(await screen.findByText("Synthetic Child")).toBeTruthy();
    setAccessToken("another-staff-same-school");
    fireEvent.focus(window);
    expect(screen.queryByText("Synthetic Child")).toBeNull();
    expect(screen.queryByRole("button", { name: "Check In" })).toBeNull();
    expect(api.checkinStudent).not.toHaveBeenCalled();
  });

  it("does not render a late old-session roster response after a school switch", async () => {
    let finishOld;
    api.fetchRosterToday.mockImplementationOnce(() => new Promise((resolve) => { finishOld = resolve; }))
      .mockResolvedValue({
        care_session: "AM", date: "2026-10-30", dow: "FRI", rows: [],
        unlinked_attendance_count: 0,
      });
    render(<AftercareRosterPage careSession="AM" />);
    await waitFor(() => expect(api.fetchRosterToday).toHaveBeenCalledTimes(1));
    setSelectedSchoolId("fictional-other-school");
    await waitFor(() => expect(api.fetchRosterToday).toHaveBeenCalledTimes(2));
    finishOld({
      care_session: "AM", date: "2026-10-30", dow: "FRI", rows,
      unlinked_attendance_count: 0,
    });
    await waitFor(() => expect(screen.getByText("No students scheduled today.")).toBeTruthy());
    expect(screen.queryByText("Synthetic Child")).toBeNull();
    expect(api.checkinStudent).not.toHaveBeenCalled();
  });

  it("blocks an AM check-in after its staff session expires or switches", async () => {
    render(<AftercareRosterPage careSession="AM" />);
    await screen.findByText("Synthetic Child");
    sessionStorage.removeItem("crown.jwt.access");
    fireEvent.focus(window);
    expect(getAccessToken()).toBe("");
    expect(screen.queryByText("Synthetic Child")).toBeNull();
    expect(api.checkinStudent).not.toHaveBeenCalled();
  });
});

it("shows unconfirmed custody and blocks repeat action after staff token switches during a pending check-in", async () => {
  let settle;
  api.checkinStudent.mockImplementation(() => new Promise((resolve) => { settle = resolve; }));
  render(<AftercareRosterPage careSession="AM" />);
  await screen.findByText("Synthetic Child");
  fireEvent.click(screen.getByRole("button", { name: "Check In" }));
  await waitFor(() => expect(api.checkinStudent).toHaveBeenCalledTimes(1));
  setAccessToken("second-staff-while-checkin-pending");
  fireEvent.focus(window);
  const warning = screen.getByRole("alert");
  expect(warning.textContent).toMatch(/outcome is unconfirmed/i);
  expect(screen.queryByText("Synthetic Child")).toBeNull();
  settle({ id: 99 });
  await waitFor(() => expect(screen.getByRole("alert").textContent).toMatch(/do not retry automatically/i));
  expect(api.checkinStudent).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("button", { name: "Review current custody before continuing" }).disabled).toBe(false);
});

it("blocks reconciliation until the prior staff custody write has settled", async () => {
  let finishWrite;
  api.checkinStudent.mockImplementation(() => new Promise((resolve) => { finishWrite = resolve; }));
  render(<AftercareRosterPage careSession="AM" />);
  await screen.findByText("Synthetic Child");
  fireEvent.click(screen.getByRole("button", { name: "Check In" }));
  await waitFor(() => expect(api.checkinStudent).toHaveBeenCalledTimes(1));

  setAccessToken("replacement-staff-token");
  fireEvent.focus(window);
  const reconcile = screen.getByRole("button", { name: "Review current custody before continuing" });
  expect(reconcile.disabled).toBe(true);
  expect(screen.getByText(/previous custody write is still pending/i)).toBeTruthy();
  const readsBefore = api.fetchRosterToday.mock.calls.length;
  fireEvent.click(reconcile);
  expect(api.fetchRosterToday).toHaveBeenCalledTimes(readsBefore);

  finishWrite({ id: 99 });
  await waitFor(() => expect(reconcile.disabled).toBe(false));
  expect(screen.getByText(/outcome is unconfirmed/i)).toBeTruthy();
  expect(api.fetchRosterToday).toHaveBeenCalledTimes(readsBefore);
  api.fetchRosterToday.mockResolvedValueOnce({
    care_session: "AM", date: "2026-10-30", dow: "FRI",
    rows: [], unlinked_attendance_count: 0,
  });
  fireEvent.click(reconcile);
  await waitFor(() => expect(api.fetchRosterToday).toHaveBeenCalledTimes(readsBefore + 1));
  await waitFor(() => expect(screen.queryByText(/outcome is unconfirmed/i)).toBeNull());
  expect(api.checkinStudent).toHaveBeenCalledTimes(1);
});

it("requires an explicit authorized readback before clearing a custody outcome warning", async () => {
  let finish;
  api.checkinStudent.mockImplementation(() => new Promise((resolve) => { finish = resolve; }));
  render(<AftercareRosterPage careSession="AM" />);
  await screen.findByText("Synthetic Child");
  fireEvent.click(screen.getByRole("button", { name: "Check In" }));
  await waitFor(() => expect(api.checkinStudent).toHaveBeenCalledTimes(1));
  setAccessToken("second-staff-while-checkin-pending");
  fireEvent.focus(window);
  finish({ id: 99 });
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  api.fetchRosterToday.mockRejectedValueOnce(new Error("Unauthorized staff"));
  fireEvent.click(screen.getByRole("button", { name: "Review current custody before continuing" }));
  await waitFor(() => expect(screen.getAllByRole("alert").some((el) => /Custody reconciliation failed/.test(el.textContent))).toBe(true));
  expect(screen.getByText(/outcome is unconfirmed/i)).toBeTruthy();
  api.fetchRosterToday.mockResolvedValueOnce({
    care_session: "AM", date: "2026-10-30", dow: "FRI",
    rows: [], unlinked_attendance_count: 0,
  });
  fireEvent.click(screen.getByRole("button", { name: "Review current custody before continuing" }));
  await waitFor(() => expect(screen.queryByText(/outcome is unconfirmed/i)).toBeNull());
  expect(api.checkinStudent).toHaveBeenCalledTimes(1);
});
