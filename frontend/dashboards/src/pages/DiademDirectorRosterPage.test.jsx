// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import DiademDirectorRosterPage from "./DiademDirectorRosterPage.jsx";
import { crownApiClient } from "../api/client.js";
import { getAccessToken, getSelectedSchoolId, setAccessToken, setSelectedSchoolId } from "../utils/authClient.js";

vi.mock("../api/client.js", () => ({
  crownApiClient: { get: vi.fn(), post: vi.fn() },
}));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children }) => <main>{children}</main>,
}));
vi.mock("../components/layout/DashboardSection.jsx", () => ({
  default: ({ children }) => <section>{children}</section>,
}));

const site = "11111111-1111-4111-8111-111111111111";
const child = "Synthetic Child";
const roster = { site_id: site, as_of: "2026-11-01T12:00:00Z", children_present: 1,
  rows: [{ attendance_id: "visit-1", child_name: child, room_name: "Toddler",
    program_code: "DAYCARE", checked_in_at: "2026-11-01T11:00:00Z" }] };

beforeEach(() => {
  vi.resetAllMocks();
  sessionStorage.setItem("crown.school.id", "synthetic-school-a");
  setAccessToken("synthetic-staff-access-token");
  crownApiClient.get.mockImplementation(async (url) =>
    url.endsWith("/sites/") ? { data: { sites: [{ site_id: site, name: "Synthetic Center", is_active: true }] } } :
      { data: roster });
});
afterEach(() => { cleanup(); sessionStorage.clear(); });

it("displays source-backed open custody without automatically releasing a child", async () => {
  render(<DiademDirectorRosterPage />);
  expect(await screen.findByText(child)).toBeTruthy();
  expect(screen.getByText(/1 open custody record/)).toBeTruthy();
  expect(crownApiClient.get).toHaveBeenCalledWith("/api/v1/aftercare/daycare/sites/");
  expect(crownApiClient.get).toHaveBeenCalledWith(`/api/v1/aftercare/daycare/sites/${site}/roster/`);
  expect(screen.getByRole("button", { name: "Review pickup" })).toBeTruthy();
  expect(crownApiClient.post).not.toHaveBeenCalled();
  expect(screen.getByRole("region", { name: "Children in care roster" }).getAttribute("tabindex")).toBe("0");
});

// These are React integration checks with a fictional mocked API. They are
// not authenticated Playwright or live-backend custody certification.
const attendanceId = "33333333-3333-4333-8333-333333333333";
const roomId = "22222222-2222-4222-8222-222222222222";
const pickupAuthorityId = "44444444-4444-4444-8444-444444444444";
const pickupRoster = {
  ...roster,
  rows: [{ ...roster.rows[0], attendance_id: attendanceId, room_id: roomId }],
};
const pickupCandidates = {
  site_id: site,
  attendance_id: attendanceId,
  status: "candidates_only",
  options: [{ authority_id: pickupAuthorityId, guardian_name: "Synthetic Guardian" }],
};

function configurePickupFlow(post) {
  let released = false;
  sessionStorage.setItem("access_token", "synthetic-staff-access-token");
  crownApiClient.get.mockImplementation(async (url) => {
    if (url.endsWith("/sites/")) {
      return { data: { sites: [{ site_id: site, name: "Synthetic Center", is_active: true }] } };
    }
    if (url.endsWith("/release-authorities/")) return { data: pickupCandidates };
    if (url.endsWith("/roster/")) {
      return { data: released ? { ...pickupRoster, children_present: 0, rows: [] } : pickupRoster };
    }
    throw new Error("Unexpected synthetic Diadem API path");
  });
  crownApiClient.post.mockImplementation(async (...args) => {
    const result = await post(...args);
    if (result?.data?.status === "released") released = true;
    return result;
  });
}

async function performPickupReview() {
  fireEvent.click(await screen.findByRole("button", { name: "Review pickup" }));
  await screen.findByText("Synthetic Guardian");
  fireEvent.change(screen.getByLabelText("Verified pickup recipient"), {
    target: { value: pickupAuthorityId },
  });
  fireEvent.change(screen.getByLabelText("Identity verification method"), {
    target: { value: "GOVERNMENT_PHOTO_ID" },
  });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Confirm verified handoff" }));
}

it("confirms the synthetic handoff, re-reads the server roster, and retains receipt feedback", async () => {
  configurePickupFlow(async () => ({
    data: { status: "released", attendance_id: attendanceId },
  }));
  render(<DiademDirectorRosterPage />);
  await performPickupReview();
  expect(await screen.findByText(/No open custody records returned for this center/)).toBeTruthy();
  expect(screen.getByText(/Server-confirmed handoff/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Review pickup" })).toBeNull();
  expect(crownApiClient.post).toHaveBeenCalledTimes(1);
  const [url, data] = crownApiClient.post.mock.calls[0];
  expect(url).toBe("/api/v1/aftercare/daycare/attendance/release/");
  expect(data).toMatchObject({
    attendance_id: attendanceId, room_id: roomId, guardian_authority_id: pickupAuthorityId,
    identity_method: "GOVERNMENT_PHOTO_ID", identity_verified: true,
  });
});

it("keeps synthetic custody open when the service refuses a selected recipient", async () => {
  configurePickupFlow(async () => { throw new Error("Recipient authorization revoked"); });
  render(<DiademDirectorRosterPage />);
  await performPickupReview();
  expect((await screen.findByRole("alert")).textContent).toMatch(/Release not confirmed/);
  expect(screen.getByText(child)).toBeTruthy();
  expect(screen.queryByText(/Server-confirmed handoff/)).toBeNull();
  expect(screen.getByRole("button", { name: "Confirm verified handoff" }).disabled).toBe(true);
  expect(crownApiClient.post).toHaveBeenCalledTimes(1);
});

it("fails closed on a mismatched site or inconsistent custody count", async () => {
  crownApiClient.get.mockImplementation(async (url) => url.endsWith("/sites/") ?
    { data: { sites: [{ site_id: site, name: "Synthetic Center", is_active: true }] } } :
    { data: { ...roster, children_present: 3 } });
  render(<DiademDirectorRosterPage />);
  expect((await screen.findByRole("alert")).textContent).toMatch(/site-scoping validation/i);
  expect(screen.queryByText(child)).toBeNull();
});

it("does not show a fabricated empty roster after a denied directory request", async () => {
  crownApiClient.get.mockRejectedValue(new Error("Not authorized"));
  render(<DiademDirectorRosterPage />);
  expect((await screen.findByRole("alert")).textContent).toContain("Not authorized");
  expect(screen.queryByText(/No open custody records returned/)).toBeNull();
});

it("refreshes server evidence without creating any custody action", async () => {
  render(<DiademDirectorRosterPage />);
  await screen.findByText(child);
  fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
  await waitFor(() => expect(crownApiClient.get).toHaveBeenCalledWith("/api/v1/aftercare/daycare/sites/"));
  expect(crownApiClient.get.mock.calls.filter(([url]) => url.endsWith("/sites/")).length).toBe(2);
});

it("never displays old site identities while switching to another center", async () => {
  const second = "22222222-2222-4222-8222-222222222222";
  let resolveSecond;
  crownApiClient.get.mockImplementation(async (url) => {
    if (url.endsWith("/sites/")) return { data: { sites: [
      { site_id: site, name: "Synthetic Center", is_active: true },
      { site_id: second, name: "Other Center", is_active: true },
    ] } };
    if (url.includes(second)) return new Promise((done) => { resolveSecond = done; });
    return { data: roster };
  });
  render(<DiademDirectorRosterPage />);
  expect(await screen.findByText(child)).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Care center"), { target: { value: second } });
  expect(screen.queryByText(child)).toBeNull();
  resolveSecond({ data: { ...roster, site_id: second, rows: [], children_present: 0 } });
  await waitFor(() => expect(screen.getByText(/0 open custody record/)).toBeTruthy());
  expect(screen.queryByText(child)).toBeNull();
});

it("clears the previous school's child roster immediately when tenant context changes", async () => {
  crownApiClient.get.mockImplementation(async (url) => {
    if (url.endsWith("/sites/")) {
      return { data: { sites: getSelectedSchoolId() === "synthetic-school-a"
        ? [{ site_id: site, name: "Synthetic Center", is_active: true }]
        : [] } };
    }
    return { data: roster };
  });
  render(<DiademDirectorRosterPage />);
  expect(await screen.findByText(child)).toBeTruthy();
  const { act } = await import("@testing-library/react");
  act(() => { setSelectedSchoolId("synthetic-school-b"); });
  expect(screen.queryByText(child)).toBeNull();
  await waitFor(() => expect(screen.getByText("No authorized childcare centers available.")).toBeTruthy());
  expect(crownApiClient.get.mock.calls.filter(([url]) => url.endsWith("/sites/")).length).toBe(2);
});

it("removes previous staff custody after a same-school access-token rotation", async () => {
  crownApiClient.get.mockImplementation(async (url) => {
    if (getAccessToken() !== "synthetic-staff-access-token")
      throw new Error("New staff session is not authorized for this roster.");
    if (url.endsWith("/sites/")) return { data: {
      sites: [{ site_id: site, name: "Synthetic Center", is_active: true }],
    } };
    return { data: roster };
  });
  render(<DiademDirectorRosterPage />);
  expect(await screen.findByText(child)).toBeTruthy();
  const { act } = await import("@testing-library/react");
  act(() => { setAccessToken("other-staff-same-school-access-token"); });
  expect(screen.queryByText(child)).toBeNull();
  expect((await screen.findByRole("alert")).textContent).toMatch(/not authorized for this roster/i);
  expect(crownApiClient.post).not.toHaveBeenCalled();
});

it("keeps interrupted custody outcome unconfirmed when staff switch during a pending POST", async () => {
  let settle;
  configurePickupFlow(() => new Promise((resolve) => { settle = resolve; }));
  const authorizedGet = crownApiClient.get.getMockImplementation();
  crownApiClient.get.mockImplementation((url) => getAccessToken() === "synthetic-staff-access-token"
    ? authorizedGet(url)
    : Promise.reject(new Error("New identity lacks the previous roster grant")));
  render(<DiademDirectorRosterPage />);
  await performPickupReview();
  await waitFor(() => expect(crownApiClient.post).toHaveBeenCalledTimes(1));
  const { act } = await import("@testing-library/react");
  act(() => { setAccessToken("different-staff-session"); });
  expect(screen.queryByText(child)).toBeNull();
  expect((await screen.findByRole("alert")).textContent).toMatch(/handoff outcome is unconfirmed/i);
  settle({ data: { status: "released", attendance_id: attendanceId } });
  await waitFor(() => expect(crownApiClient.post).toHaveBeenCalledTimes(1));
  expect(screen.queryByText(/Server-confirmed handoff/)).toBeNull();
  expect(screen.getByText(/Do not retry automatically/)).toBeTruthy();
});
