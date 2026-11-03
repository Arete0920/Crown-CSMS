// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import SummerCampDemoRegistration from "./SummerCampDemoRegistration.jsx";
import { apiFetch } from "../lib/api.js";
import { createSummerCampEnrollment, fetchSummerCampEnrollments } from "../api/summerCampApi.js";
import { setAccessToken, setSelectedSchoolId } from "../utils/authClient.js";
vi.mock("../lib/api.js", () => ({ apiFetch: vi.fn() }));
vi.mock("../api/summerCampApi.js", () => ({ createSummerCampEnrollment: vi.fn(), fetchSummerCampEnrollments: vi.fn() }));
const SCHOOL = "19801b59-8c05-4c84-9312-5d792e4e839d";
const session = { id: 7, status: "PUBLISHED", price_cents: 0, deposit_cents: 0 };
const saved = { id: 12, school: SCHOOL, session: 7, student: "fictional-student", readiness_status: "BLOCKED", payment_status: "NOT_BILLED", balance_due_cents: 0 };
beforeEach(() => {
  vi.stubEnv("VITE_LOCAL_DEMO", "1"); setSelectedSchoolId(SCHOOL); setAccessToken("fictional-staff");
  apiFetch.mockResolvedValue({ ok: true, json: async () => [{ id: saved.student, first_name: "Fictional", last_name: "Camper", grade_level: "7", is_active: true }] });
  createSummerCampEnrollment.mockResolvedValue(saved); fetchSummerCampEnrollments.mockResolvedValue([saved]);
});
afterEach(() => { cleanup(); vi.resetAllMocks(); vi.unstubAllEnvs(); sessionStorage.clear(); });
it("verifies an independent saved GET before presenting registration success", async () => {
  const onSaved = vi.fn(); render(<SummerCampDemoRegistration session={session} rows={[]} onSaved={onSaved} />);
  await screen.findByRole("option", { name: "Fictional Camper (Grade 7)" });
  fireEvent.change(screen.getByRole("combobox"), { target: { value: saved.student } });
  fireEvent.click(screen.getByRole("button", { name: "Save fictional registration" }));
  await screen.findByText(/Registration saved and verified/);
  expect(createSummerCampEnrollment).toHaveBeenCalledExactlyOnceWith({ session_id: 7, student_id: saved.student, registration_source: "EXISTING" });
  expect(fetchSummerCampEnrollments).toHaveBeenCalledExactlyOnceWith({ session_id: 7 }); expect(onSaved).toHaveBeenCalledTimes(1);
});
it("locks retry when independent readback belongs to another session", async () => {
  fetchSummerCampEnrollments.mockResolvedValue([{ ...saved, session: 99 }]);
  const onSaved = vi.fn(); render(<SummerCampDemoRegistration session={session} rows={[]} onSaved={onSaved} />);
  await screen.findByRole("option", { name: "Fictional Camper (Grade 7)" });
  fireEvent.change(screen.getByRole("combobox"), { target: { value: saved.student } });
  fireEvent.click(screen.getByRole("button", { name: "Save fictional registration" }));
  await screen.findByRole("alert"); expect(onSaved).not.toHaveBeenCalled();
  expect(screen.getByRole("button", { name: "Save fictional registration" }).disabled).toBe(true);
});
it("invalidates choices through the actual same-tab token producer", async () => {
  render(<SummerCampDemoRegistration session={session} rows={[]} onSaved={vi.fn()} />);
  await screen.findByRole("option", { name: "Fictional Camper (Grade 7)" });
  act(() => setAccessToken("different-staff"));
  expect(screen.queryByRole("option", { name: "Fictional Camper (Grade 7)" })).toBeNull();
  expect(screen.getByRole("button", { name: "Save fictional registration" }).disabled).toBe(true);
  expect(createSummerCampEnrollment).not.toHaveBeenCalled();
});
it("does not present registration outside the explicit free local workflow", () => {
  vi.stubEnv("VITE_LOCAL_DEMO", "0"); render(<SummerCampDemoRegistration session={session} rows={[]} onSaved={vi.fn()} />);
  expect(screen.queryByRole("button", { name: "Save fictional registration" })).toBeNull(); expect(apiFetch).not.toHaveBeenCalled();
});
