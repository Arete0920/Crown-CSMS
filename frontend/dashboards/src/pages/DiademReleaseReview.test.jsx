// @vitest-environment jsdom
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import DiademReleaseReview from "./DiademReleaseReview.jsx";
import { crownApiClient } from "../api/client.js";
import { setAccessToken, setSelectedSchoolId } from "../utils/authClient.js";

vi.mock("../api/client.js", () => ({ crownApiClient: { get: vi.fn(), post: vi.fn() } }));
const site = "11111111-1111-4111-8111-111111111111";
const room = "22222222-2222-4222-8222-222222222222";
const attendanceId = "33333333-3333-4333-8333-333333333333";
const authority = "44444444-4444-4444-8444-444444444444";
const attendance = { attendance_id: attendanceId, room_id: room, child_name: "Synthetic Child" };
const candidate = { site_id: site, attendance_id: attendanceId, status: "candidates_only",
  options: [{ authority_id: authority, guardian_name: "Synthetic Guardian" }] };
const show = () => { const released = vi.fn(); render(
  <DiademReleaseReview siteId={site} attendance={attendance} onCancel={vi.fn()} onReleased={released} />
); return released; };
beforeEach(() => {
  vi.resetAllMocks();
  sessionStorage.setItem("crown.school.id", "synthetic-school-a");
  sessionStorage.setItem("access_token", "synthetic-test-access-token");
  crownApiClient.get.mockResolvedValue({ data: candidate });
  crownApiClient.post.mockResolvedValue({ data: { status: "released", attendance_id: attendanceId } });
});
afterEach(() => { cleanup(); sessionStorage.clear(); });

it("requires actual recipient selection, method and identity attestation", async () => {
  const released = show();
  expect(await screen.findByText("Synthetic Guardian")).toBeTruthy();
  const submit = screen.getByRole("button", { name: "Confirm verified handoff" });
  expect(submit.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText("Verified pickup recipient"), { target: { value: authority } });
  fireEvent.change(screen.getByLabelText("Identity verification method"), { target: { value: "GOVERNMENT_PHOTO_ID" } });
  expect(submit.disabled).toBe(true);
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(submit);
  await waitFor(() => expect(released).toHaveBeenCalledTimes(1));
  expect(crownApiClient.post).toHaveBeenCalledTimes(1);
  const [url, data] = crownApiClient.post.mock.calls[0];
  expect(url).toBe("/api/v1/aftercare/daycare/attendance/release/");
  expect(data).toMatchObject({ site_id: site, room_id: room, attendance_id: attendanceId,
    guardian_authority_id: authority, identity_method: "GOVERNMENT_PHOTO_ID", identity_verified: true });
  expect(data.request_key).toMatch(/^[0-9a-f-]{36}$/i);
  expect(data).not.toHaveProperty("school_id");
});

it("blocks ordinary release when care date changes", async () => {
  crownApiClient.get.mockResolvedValue({ data: { ...candidate,
    status: "overnight_director_review_required", options: [] } });
  show();
  expect(await screen.findByText(/Care date changed/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Confirm verified handoff" })).toBeNull();
  expect(crownApiClient.post).not.toHaveBeenCalled();
});

it("blocks release without any verified recipient", async () => {
  crownApiClient.get.mockResolvedValue({ data: { ...candidate, options: [] } });
  show();
  expect(await screen.findByText(/No verified recipient available/)).toBeTruthy();
  expect(crownApiClient.post).not.toHaveBeenCalled();
});

it("rejects a mismatched attendance response", async () => {
  crownApiClient.get.mockResolvedValue({ data: { ...candidate, attendance_id: "foreign" } });
  show();
  expect((await screen.findByRole("alert")).textContent).toMatch(/failed custody scope/);
  expect(crownApiClient.post).not.toHaveBeenCalled();
});

it("does not show stale recipient information after tenant switch", async () => {
  let resolve;
  crownApiClient.get.mockImplementation(() => new Promise((done) => { resolve = done; }));
  show();
  setSelectedSchoolId("synthetic-school-b");
  resolve({ data: candidate });
  await waitFor(() => expect(crownApiClient.get).toHaveBeenCalledTimes(1));
  expect(screen.queryByText("Synthetic Guardian")).toBeNull();
  expect(crownApiClient.post).not.toHaveBeenCalled();
});

it("fails closed with explicit guidance when staff credentials change before confirmation", async () => {
  const released = show();
  await screen.findByText("Synthetic Guardian");
  fireEvent.change(screen.getByLabelText("Verified pickup recipient"), { target: { value: authority } });
  fireEvent.change(screen.getByLabelText("Identity verification method"), { target: { value: "GOVERNMENT_PHOTO_ID" } });
  fireEvent.click(screen.getByRole("checkbox"));
  setAccessToken("rotated-staff-access-token");
  fireEvent.click(screen.getByRole("button", { name: "Confirm verified handoff" }));
  expect(screen.getByRole("alert").textContent).toMatch(/staff session or school context changed/i);
  expect(crownApiClient.post).not.toHaveBeenCalled();
  expect(released).not.toHaveBeenCalled();
  expect(screen.getByRole("button", { name: "Confirm verified handoff" }).disabled).toBe(true);
});

it("keeps custody unconfirmed and allows cancel when identity changes during a pending POST", async () => {
  let resolvePost;
  crownApiClient.post.mockImplementation(() => new Promise((resolve) => { resolvePost = resolve; }));
  const released = show();
  await screen.findByText("Synthetic Guardian");
  fireEvent.change(screen.getByLabelText("Verified pickup recipient"), { target: { value: authority } });
  fireEvent.change(screen.getByLabelText("Identity verification method"), { target: { value: "GOVERNMENT_PHOTO_ID" } });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Confirm verified handoff" }));
  await waitFor(() => expect(crownApiClient.post).toHaveBeenCalledTimes(1));
  expect(screen.getByRole("button", { name: "Cancel review" }).disabled).toBe(true);
  setAccessToken("new-staff-access-token-after-submit");
  resolvePost({ data: { status: "released", attendance_id: attendanceId } });
  expect((await screen.findByRole("alert")).textContent).toMatch(/handoff outcome is unconfirmed/i);
  await waitFor(() => expect(screen.getByRole("button", { name: "Cancel review" }).disabled).toBe(false));
  expect(screen.getByRole("button", { name: "Confirm verified handoff" }).disabled).toBe(true);
  expect(released).not.toHaveBeenCalled();
  expect(crownApiClient.post).toHaveBeenCalledTimes(1);
});

it("does not retry ambiguous release responses", async () => {
  crownApiClient.post.mockResolvedValue({ data: { status: "released", attendance_id: "other" } });
  const released = show();
  await screen.findByText("Synthetic Guardian");
  fireEvent.change(screen.getByLabelText("Verified pickup recipient"), { target: { value: authority } });
  fireEvent.change(screen.getByLabelText("Identity verification method"), { target: { value: "GOVERNMENT_PHOTO_ID" } });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.click(screen.getByRole("button", { name: "Confirm verified handoff" }));
  expect((await screen.findByRole("alert")).textContent).toMatch(/Release not confirmed/);
  expect(released).not.toHaveBeenCalled();
  expect(crownApiClient.post).toHaveBeenCalledTimes(1);
  expect(screen.getByRole("button", { name: "Confirm verified handoff" }).disabled).toBe(true);
});
