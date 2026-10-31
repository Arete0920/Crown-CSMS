// @vitest-environment jsdom
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import SummerCampRosterPage from "./SummerCampRosterPage.jsx";
import * as api from "../api/summerCampApi.js";

vi.mock("../api/summerCampApi.js", () => ({
  fetchSummerCampSessions: vi.fn(),
  fetchSummerCampSessionRoster: vi.fn(),
  fetchSummerCampRosterToday: vi.fn(),
  fetchCampPickupChoices: vi.fn(),
  checkinSummerCamper: vi.fn(),
  checkoutSummerCamper: vi.fn(),
}));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <main>{children}</main>,
}));
vi.mock("../components/layout/DashboardSection.jsx", () => ({
  default: ({ children }) => <section>{children}</section>,
}));

const registration = {
  enrollment_id: "11", student_id: "student-1", student_name: "Synthetic Camper",
  status: "REGISTERED", readiness_status: "READY",
};
const session = {
  id: 7, name: "Synthetic Camp Week", status: "PUBLISHED",
  start_date: "2026-07-01", end_date: "2026-07-07",
};
const attendance = {
  enrollment_id: "11", session_id: "7", student_id: "student-1",
  checkin_time: "2026-07-02T08:00:00-04:00", checkout_time: null, pickup_verified: false,
};

function setCustody(entries = [attendance]) {
  api.fetchSummerCampRosterToday.mockResolvedValue({ date: "2026-07-02", rows: entries });
}

beforeEach(() => {
  api.fetchSummerCampSessions.mockResolvedValue([session]);
  api.fetchSummerCampSessionRoster.mockResolvedValue({ session_id: "7", rows: [registration] });
  setCustody();
  api.fetchCampPickupChoices.mockResolvedValue({
    enrollment_id: 11, contacts: [{ id: 42, name: "Approved Adult", relationship: "Guardian" }],
  });
  api.checkoutSummerCamper.mockResolvedValue({ attendance_id: 12 });
  api.checkinSummerCamper.mockResolvedValue({ attendance_id: 12 });
});
afterEach(() => { cleanup(); vi.resetAllMocks(); });

describe("Summer Camp roster integrated custody UI", () => {
  it("requires selecting a current contact and an explicit identity attestation to release", async () => {
    render(<SummerCampRosterPage />);
    const verify = await screen.findByRole("button", { name: "Verify pickup" });
    expect(verify.disabled).toBe(false);
    fireEvent.click(verify);
    const panel = await screen.findByRole("region", { name: "Verify Camp pickup" });
    const release = within(panel).getByRole("button", { name: "Record verified release" });
    expect(release.disabled).toBe(true);
    fireEvent.change(within(panel).getByLabelText("Authorized person"), { target: { value: "42" } });
    expect(release.disabled).toBe(true);
    fireEvent.click(within(panel).getByLabelText(/personally verified/i));
    expect(release.disabled).toBe(false);
    fireEvent.click(release);
    await waitFor(() => expect(api.checkoutSummerCamper).toHaveBeenCalledWith({
      session_id: 7, student_id: "student-1", pickup_contact_id: 42, pickup_verified: true,
    }));
    expect(api.checkoutSummerCamper).toHaveBeenCalledTimes(1);
  });

  it("blocks release when no current authorized contacts exist", async () => {
    api.fetchCampPickupChoices.mockResolvedValue({ enrollment_id: 11, contacts: [] });
    render(<SummerCampRosterPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Verify pickup" }));
    const panel = await screen.findByRole("region", { name: "Verify Camp pickup" });
    expect(within(panel).getByRole("alert").textContent).toMatch(/release blocked/i);
    expect(within(panel).getByRole("button", { name: "Record verified release" }).disabled).toBe(true);
    expect(api.checkoutSummerCamper).not.toHaveBeenCalled();
  });

  it("fails closed on missing custody evidence and permits explicit reload", async () => {
    api.fetchSummerCampRosterToday.mockRejectedValueOnce(new Error("Unavailable"));
    render(<SummerCampRosterPage />);
    await waitFor(() => expect(screen.getByText(/Unavailable/)).toBeTruthy());
    expect(screen.queryByRole("button", { name: "Verify pickup" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Refresh custody roster" }));
    expect(await screen.findByRole("button", { name: "Verify pickup" })).toBeTruthy();
    expect(api.fetchSummerCampRosterToday).toHaveBeenCalledTimes(2);
  });

  it("denies release and check-in for duplicate current registrations", async () => {
    api.fetchSummerCampSessionRoster.mockResolvedValue({
      session_id: "7", rows: [registration, { ...registration, enrollment_id: "12" }],
    });
    render(<SummerCampRosterPage />);
    await screen.findAllByText("Synthetic Camper");
    for (const button of screen.getAllByRole("button", { name: "Verify pickup" })) {
      expect(button.disabled).toBe(true);
    }
    for (const button of screen.getAllByRole("button", { name: "Check in" })) {
      expect(button.disabled).toBe(true);
    }
    expect(api.fetchCampPickupChoices).not.toHaveBeenCalled();
  });

  it("keeps session switching disabled while an authorized-contact lookup is pending", async () => {
    let finish;
    api.fetchCampPickupChoices.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
    render(<SummerCampRosterPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Verify pickup" }));
    const selector = screen.getByLabelText("Session:");
    await waitFor(() => expect(selector.disabled).toBe(true));
    finish({ enrollment_id: 11, contacts: [{ id: 42, name: "Approved Adult", relationship: "Guardian" }] });
    await waitFor(() => expect(selector.disabled).toBe(false));
  });
});
