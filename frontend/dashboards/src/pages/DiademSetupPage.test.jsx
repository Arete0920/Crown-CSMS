// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import DiademSetupPage from "./DiademSetupPage.jsx";
import { crownApiClient } from "../api/client.js";
import { clearBrowserAuthState, setSelectedSchoolId } from "../utils/authClient.js";

vi.mock("../api/client.js", () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
vi.mock("../components/crown/CrownLayout.jsx", () => ({ default: ({ children }) => <main>{children}</main> }));
const BASE = "/api/v1/aftercare/daycare/setup/sites/";
const site = { site_id: "site-a", code: "north", name: "Synthetic Center", is_active: false,
  operating_mode: "STANDALONE", jurisdiction: "US-DE" };
let sites;
let rooms;
const directory = () => ({ data: { school_id: "school-a", as_of: "2026-11-02T12:00:00Z", source: "aftercare.DaycareSite", sites } });
const roomRead = (siteId = "site-a") => ({ data: { school_id: "school-a", site_id: siteId,
  as_of: "2026-11-02T12:00:01Z", source: "aftercare.DaycareRoom", rooms } });
beforeEach(() => {
  vi.resetAllMocks(); sites = []; rooms = [];
  sessionStorage.setItem("crown.school.id", "school-a"); sessionStorage.setItem("crown.jwt.access", "synthetic-test-token");
  crownApiClient.get.mockImplementation(async (url) => url === BASE ? directory() : roomRead());
  crownApiClient.post.mockImplementation(async (url, payload) => {
    if (url === BASE) sites = [{ ...site, ...payload }];
    else rooms = [{ ...payload, room_id: "room-a", is_active: false, policy_verified_at: null }];
    return { data: url === BASE ? sites[0] : rooms[0], status: 201 };
  });
});
afterEach(() => { cleanup(); sessionStorage.clear(); });

it("creates an inactive center and room then displays actual GET readback", async () => {
  render(<DiademSetupPage />); await screen.findByText("No centers configured.");
  fireEvent.change(screen.getByLabelText("Center name"), { target: { value: site.name } });
  fireEvent.change(screen.getByLabelText("Center code"), { target: { value: "north" } });
  fireEvent.change(screen.getByLabelText("Operating mode"), { target: { value: "STANDALONE" } });
  fireEvent.click(screen.getByRole("button", { name: "Save inactive center" }));
  await screen.findByText(/Synthetic Center — inactive/);
  expect(crownApiClient.post).toHaveBeenCalledWith(BASE, { code: "north", name: site.name, operating_mode: "STANDALONE", jurisdiction: "US-DE" });
  await screen.findByText("No room records returned.");
  fireEvent.change(screen.getByLabelText("Room name"), { target: { value: "Synthetic Room" } });
  fireEvent.change(screen.getByLabelText("Room code"), { target: { value: "toddler" } });
  fireEvent.change(screen.getByLabelText("Proposed licensed capacity"), { target: { value: "12" } });
  fireEvent.click(screen.getByRole("button", { name: "Save inactive room" }));
  await screen.findByText(/Synthetic Room — inactive; capacity 12/);
  expect(crownApiClient.post.mock.calls[1][1]).toMatchObject({ licensed_capacity: 12, proposed_min_age_months: null, proposed_policy_from: null });
  expect(crownApiClient.post.mock.calls[1][1]).not.toHaveProperty("is_active");
  expect(screen.getByText(/Rooms observed at.*aftercare.DaycareRoom/)).toBeTruthy();
});

it("does not expose forms or invented empty results when configuration is denied", async () => {
  crownApiClient.get.mockRejectedValue(new Error("Permission denied"));
  render(<DiademSetupPage />);
  expect((await screen.findByRole("alert")).textContent).toContain("Permission denied");
  expect(screen.queryByText("No centers configured.")).toBeNull();
  expect(screen.queryByRole("button", { name: "Save inactive center" })).toBeNull();
});

it("rejects mismatched tenant and room readback without rendering records", async () => {
  sites = [site];
  crownApiClient.get.mockImplementation(async (url) => url === BASE ? directory() :
    { data: { ...roomRead().data, site_id: "foreign", rooms: [{ room_id: "x", name: "Foreign private room" }] } });
  render(<DiademSetupPage />);
  expect((await screen.findByRole("alert")).textContent).toContain("scope");
  expect(screen.queryByText(/Foreign private room/)).toBeNull();
  expect(screen.queryByText("No room records returned.")).toBeNull();
});

it("suppresses an old directory response after school changes", async () => {
  let release;
  crownApiClient.get.mockReturnValue(new Promise((resolve) => { release = resolve; }));
  render(<DiademSetupPage />);
  await waitFor(() => expect(crownApiClient.get).toHaveBeenCalled());
  act(() => { setSelectedSchoolId("school-b"); });
  await act(async () => release({ data: { ...directory().data, sites: [site] } }));
  expect(screen.queryByText(/Synthetic Center —/)).toBeNull();
  expect(screen.queryByRole("button", { name: "Save inactive center" })).toBeNull();
});

it("removes readback and unsaved forms on session clearing", async () => {
  sites = [site]; render(<DiademSetupPage />);
  await screen.findByText(/Synthetic Center — inactive/);
  fireEvent.change(screen.getByLabelText("Center name"), { target: { value: "Unsaved" } });
  act(() => { clearBrowserAuthState(); });
  expect(screen.queryByText(/Synthetic Center —/)).toBeNull();
  expect(screen.queryByDisplayValue("Unsaved")).toBeNull();
});

it("clears a pending loading view when the browser session is removed", async () => {
  crownApiClient.get.mockReturnValue(new Promise(() => {}));
  render(<DiademSetupPage />);
  await screen.findByText("Loading or saving configuration…");
  act(() => { clearBrowserAuthState(); });
  expect(screen.queryByText("Loading or saving configuration…")).toBeNull();
  expect(screen.queryByRole("button", { name: "Save inactive center" })).toBeNull();
});

it("an earlier room GET cannot overwrite the post-save authoritative readback", async () => {
  sites = [site]; let oldRead;
  crownApiClient.get.mockImplementation(async (url) => {
    if (url === BASE) return directory();
    if (!oldRead) return new Promise((resolve) => { oldRead = resolve; });
    return roomRead();
  });
  render(<DiademSetupPage />);
  await screen.findByLabelText("Room name");
  await waitFor(() => expect(oldRead).toBeTypeOf("function"));
  fireEvent.change(screen.getByLabelText("Room name"), { target: { value: "New Room" } });
  fireEvent.change(screen.getByLabelText("Room code"), { target: { value: "new-room" } });
  fireEvent.click(screen.getByRole("button", { name: "Save inactive room" }));
  await screen.findByText(/New Room — inactive/);
  await act(async () => oldRead({ data: { ...roomRead().data, rooms: [] } }));
  expect(screen.getByText(/New Room — inactive/)).toBeTruthy();
});
