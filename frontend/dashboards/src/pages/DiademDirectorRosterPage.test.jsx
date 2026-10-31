// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import DiademDirectorRosterPage from "./DiademDirectorRosterPage.jsx";
import { crownApiClient } from "../api/client.js";

vi.mock("../api/client.js", () => ({
  crownApiClient: { get: vi.fn(), post: vi.fn() },
}));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <div>{children}</div>,
}));
vi.mock("../components/layout/DashboardSection.jsx", () => ({
  default: ({ title, children }) => <section aria-label={title}>{children}</section>,
}));

const root = "/api/v1/aftercare/daycare";
const sites = [{ site_id: "site-1", name: "Synthetic Childcare", is_active: true }];
const openRow = {
  attendance_id: "attendance-1", child_id: "child-1", child_name: "Sample Child",
  room_id: "room-1", room_name: "Toddler Room",
  program_code: "DAYCARE", checked_in_at: "2026-10-31T08:00:00Z",
};
const scheduledRow = {
  enrollment_id: "enrollment-1", child_id: "child-2", child_name: "Second Child",
  room_id: "room-1", room_name: "Toddler Room", program_code: "DAYCARE",
};

function liveGet(url) {
  if (url === root + "/sites/") return Promise.resolve({ data: { sites } });
  if (url === root + "/sites/site-1/roster/") return Promise.resolve({
    data: { site_id: "site-1", as_of: "2026-10-31T09:00:00Z",
      children_present: 1, rows: [openRow] },
  });
  if (url === root + "/sites/site-1/scheduled/") return Promise.resolve({
    data: { site_id: "site-1", rows: [scheduledRow] },
  });
  if (url === root + "/attendance/attendance-1/pickup-authorities/") return Promise.resolve({
    data: { attendance_id: "attendance-1", recipients: [
      { guardian_authority_id: "authority-1", guardian_name: "Approved Guardian" },
    ] },
  });
  return Promise.reject(new Error("Unrecognized synthetic route: " + url));
}

beforeEach(() => {
  vi.resetAllMocks();
  vi.stubGlobal("crypto", { randomUUID: vi.fn(() => "00000000-0000-4000-8000-000000000001") });
  crownApiClient.get.mockImplementation(liveGet);
  crownApiClient.post.mockResolvedValue({ status: 201, data: {} });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

async function openPickup() {
  fireEvent.click(await screen.findByRole("button", { name: "Verify authorized pickup" }));
  await screen.findByRole("option", { name: "Approved Guardian" });
}

describe("Diadem staff physical custody controls", () => {
  it("shows only server-backed open custody and scheduled child records", async () => {
    render(<DiademDirectorRosterPage />);
    expect(await screen.findByText("Sample Child")).toBeTruthy();
    expect(await screen.findByText("Second Child")).toBeTruthy();
    expect(screen.getByText(/1 open custody record/)).toBeTruthy();
    expect(crownApiClient.get).toHaveBeenCalledWith(root + "/sites/site-1/roster/");
    expect(crownApiClient.get).toHaveBeenCalledWith(root + "/sites/site-1/scheduled/");
  });

  it("requires explicit guardian choice, identity method, and attestation", async () => {
    render(<DiademDirectorRosterPage />);
    await openPickup();
    const release = screen.getByRole("button", { name: "Record verified release" });
    expect(release.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Authorized pickup recipient"), {
      target: { value: "authority-1" },
    });
    expect(release.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Identity verification method"), {
      target: { value: "GOVERNMENT_PHOTO_ID" },
    });
    expect(release.disabled).toBe(true);
    fireEvent.click(screen.getByLabelText(/I personally verified this individual/));
    expect(release.disabled).toBe(false);
    fireEvent.click(release);
    await waitFor(() => expect(crownApiClient.post).toHaveBeenCalledTimes(1));
    const [url, payload] = crownApiClient.post.mock.calls[0];
    expect(url).toBe(root + "/attendance/release/");
    expect(payload).toMatchObject({
      site_id: "site-1", room_id: "room-1", attendance_id: "attendance-1",
      guardian_authority_id: "authority-1", identity_verified: true,
      identity_method: "GOVERNMENT_PHOTO_ID",
    });
    expect(typeof payload.request_key).toBe("string");
  });

  it("does not treat an unknown release result as a confirmed denial or allow blind retry", async () => {
    crownApiClient.post.mockRejectedValueOnce(new Error("Network connection lost"));
    render(<DiademDirectorRosterPage />);
    await openPickup();
    fireEvent.change(screen.getByLabelText("Authorized pickup recipient"), {
      target: { value: "authority-1" },
    });
    fireEvent.change(screen.getByLabelText("Identity verification method"), {
      target: { value: "PERSONALLY_KNOWN" },
    });
    fireEvent.click(screen.getByLabelText(/I personally verified this individual/));
    fireEvent.click(screen.getByRole("button", { name: "Record verified release" }));
    expect(await screen.findByText(/Release outcome NOT CONFIRMED/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Record verified release" }).disabled).toBe(true);
    expect(screen.getByRole("button", { name: "Verify authorized pickup" }).disabled).toBe(true);
    expect(crownApiClient.post).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Refresh from server" }));
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Verify authorized pickup" }).disabled).toBe(false);
    });
  });

  it("blocks repeated check-in after an uncertain write until roster refresh", async () => {
    crownApiClient.post.mockRejectedValueOnce(new Error("Request timed out"));
    render(<DiademDirectorRosterPage />);
    const button = await screen.findByRole("button", { name: "Record check-in" });
    fireEvent.click(button);
    expect(await screen.findByText(/Check-in outcome needs verification/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Record check-in" }).disabled).toBe(true);
    expect(crownApiClient.post).toHaveBeenCalledTimes(1);
  });

  it("cancels a pickup without making a release request", async () => {
    render(<DiademDirectorRosterPage />);
    await openPickup();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("group", { name: "Verify child release" })).toBeNull();
    expect(crownApiClient.post).not.toHaveBeenCalled();
  });
  it("preserves supervised pickup when the suspended-school schedule is denied", async () => {
    crownApiClient.get.mockImplementation((url) =>
      url.endsWith("/scheduled/")
        ? Promise.reject({ response: { status: 403, data: { detail: "Admission disabled" } } })
        : liveGet(url)
    );
    render(<DiademDirectorRosterPage />);
    const open = await screen.findByRole("button", { name: "Verify authorized pickup" });
    await waitFor(() => expect(open.disabled).toBe(false));
    expect(screen.queryByRole("button", { name: "Record check-in" })).toBeNull();
    expect(screen.getByText(/Scheduled intake unavailable or unauthorized/)).toBeTruthy();
    fireEvent.click(open);
    await screen.findByRole("option", { name: "Approved Guardian" });
    expect(screen.getByRole("button", { name: "Record verified release" }).disabled).toBe(true);
  });

});
