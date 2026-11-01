// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import DiademDirectorRosterPage from "./DiademDirectorRosterPage.jsx";
import { crownApiClient } from "../api/client.js";

vi.mock("../api/client.js", () => ({
  crownApiClient: { get: vi.fn() },
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
  crownApiClient.get.mockImplementation(async (url) =>
    url.endsWith("/sites/") ? { data: { sites: [{ site_id: site, name: "Synthetic Center", is_active: true }] } } :
      { data: roster });
});
afterEach(cleanup);

it("displays source-backed open custody without any release or check-in controls", async () => {
  render(<DiademDirectorRosterPage />);
  expect(await screen.findByText(child)).toBeTruthy();
  expect(screen.getByText(/1 open custody record/)).toBeTruthy();
  expect(crownApiClient.get).toHaveBeenCalledWith("/api/v1/aftercare/daycare/sites/");
  expect(crownApiClient.get).toHaveBeenCalledWith(`/api/v1/aftercare/daycare/sites/${site}/roster/`);
  expect(screen.queryByRole("button", { name: /release|check in/i })).toBeNull();
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
