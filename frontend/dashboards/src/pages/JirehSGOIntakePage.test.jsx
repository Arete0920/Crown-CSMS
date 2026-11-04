// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import JirehSGOIntakePage from "./JirehSGOIntakePage.jsx";
import { authenticatedFetch, getAccessToken } from "../utils/authClient.js";
vi.mock("../utils/authClient.js", () => ({
  authenticatedFetch: vi.fn(),
  getAccessToken: vi.fn(),
}));
vi.mock("../components/crown/CrownLayout.jsx", () => ({
  default: ({ children, title }) => <main aria-label={title}>{children}</main>,
}));
const response = (data) => ({ json: async () => data });
const PID = "12dc4c1b-0b8a-4db0-82aa-0ed85c7a05a1";
const APP = "f56f0ca3-964f-457f-8e78-a6f73a5a2cc1";
const FAMILY = {
  id: PID, organization_id: "55036c89-efda-40c2-9b6f-3f2bb8c23adc",
  organization: "Fictional SGO A", name: "Synthetic 2027",
  calendar_year: 2027, policy_version: "DEMO_POLICY_2027_V1",
  consent_version: "DEMO_CONSENT_V1", application_id: null,
};
const saved = {
  id: APP, program_id: PID, status: "SUBMITTED", revision: 1,
  grade_level: "K", consent_version: "DEMO_CONSENT_V1",
  consented_at: "2026-11-02T12:00:00Z", funds_status: "NONCASH_ONLY",
};
beforeEach(() => {
  vi.stubEnv("VITE_LOCAL_DEMO", "1");
  vi.stubGlobal("crypto", { randomUUID: () => "2eaceaaa-cdd8-4fce-a66a-cf4938bd742b" });
  getAccessToken.mockReturnValue("family-session-a");
});
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});
describe("Jireh SGO interactive fictional intake", () => {
  it.each([false, true])("submits explicitly consented application and shows persisted readback (hosted=%s)", async (hosted) => {
    vi.stubEnv("VITE_LOCAL_DEMO", hosted ? "0" : "1");
    vi.stubEnv("VITE_HOSTED_JIREH_DEMO", hosted ? "1" : "0");
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) {
        return response({ programs: [FAMILY], synthetic_only: true, funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/processor/programs/")) {
        if (hosted) throw Object.assign(new Error("Not found"), { status: 404 });
        return response({ programs: [], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/family/submit/")) return response({ application: saved, created: true });
      if (url.includes("/family/applications/")) return response({ application: saved });
      throw new Error("unexpected fictional endpoint: " + url);
    });
    render(<JirehSGOIntakePage />);
    expect((await screen.findByLabelText("Partner SGO and program")).style.maxWidth).toBe("100%");
    const submit = screen.getByRole("button", { name: "Submit fictional application" });
    expect(submit.disabled).toBe(true);
    fireEvent.click(screen.getByRole("checkbox"));
    expect(submit.disabled).toBe(false);
    fireEvent.click(submit);
    await waitFor(() => expect(authenticatedFetch.mock.calls.some(
      ([url, opts]) => url.endsWith("/family/submit/") && opts.method === "POST"
        && opts.omitSchoolContext === !hosted
        && JSON.parse(opts.body).consent_version === "DEMO_CONSENT_V1",
    )).toBe(true));
    expect(await screen.findByText(/Persistent application readback/)).toBeTruthy();
    await waitFor(() => expect(screen.getByText((_, element) =>
      element?.tagName === "P" && element.textContent.includes("Status:")
      && element.textContent.includes("SUBMITTED")
      && element.textContent.includes("revision: 1"))).toBeTruthy());
    expect(authenticatedFetch.mock.calls.some(([url]) =>
      url.endsWith("/family/applications/" + APP + "/"))).toBe(true);
  });
  it("conceals previous family case when signed-in principal changes", async () => {
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) {
        return response({ programs: [{ ...FAMILY, application_id: APP }], synthetic_only: true, funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/processor/programs/")) {
        return response({ programs: [], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY" });
      }
      return response({ application: saved });
    });
    const view = render(<JirehSGOIntakePage />);
    expect(await screen.findByText(/Persistent application readback/)).toBeTruthy();
    getAccessToken.mockReturnValue("family-session-b");
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) return response({
        programs: [], synthetic_only: true, funds_status: "NONCASH_ONLY",
      });
      return response({ programs: [], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY" });
    });
    view.rerender(<JirehSGOIntakePage />);
    expect(screen.queryByText(/Persistent application readback/)).toBeNull();
    expect(await screen.findByText(/No fictional family grants/)).toBeTruthy();
  });
  it("confirms a family correction only after independent saved-state readback", async () => {
    const requested = { ...saved, status: "CORRECTION_REQUESTED", revision: 2,
      correction_reason: "GRADE_UNVERIFIED" };
    const resubmitted = { ...saved, status: "RESUBMITTED", revision: 3, grade_level: "2" };
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) return response({
        programs: [{ ...FAMILY, application_id: APP }], synthetic_only: true, funds_status: "NONCASH_ONLY",
      });
      if (url.endsWith("/processor/programs/")) return response({
        programs: [], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY",
      });
      if (url.endsWith("/correct/")) return response({ application: resubmitted, changed: true });
      if (url.includes("/family/applications/")) {
        return response({ application: authenticatedFetch.mock.calls.some(([u]) => u.endsWith("/correct/"))
          ? resubmitted : requested });
      }
      throw new Error("unexpected endpoint " + url);
    });
    render(<JirehSGOIntakePage />);
    expect(await screen.findByRole("button", { name: "Save correction and resubmit" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Correct or confirm fictional grade"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Save correction and resubmit" }));
    expect(await screen.findByText(/Correction saved, read back and resubmitted/)).toBeTruthy();
    await waitFor(() => expect(screen.getByText((_, el) => el?.tagName === "P"
      && el.textContent.includes("RESUBMITTED") && el.textContent.includes("revision: 3"))).toBeTruthy());
    expect(authenticatedFetch.mock.calls.filter(([url]) =>
      url.endsWith("/family/applications/" + APP + "/")).length).toBeGreaterThanOrEqual(2);
  });
  it("does not confirm correction when independent readback is stale", async () => {
    const requested = { ...saved, status: "CORRECTION_REQUESTED", revision: 2,
      correction_reason: "GRADE_UNVERIFIED" };
    const resubmitted = { ...saved, status: "RESUBMITTED", revision: 3, grade_level: "2" };
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) return response({
        programs: [{ ...FAMILY, application_id: APP }], synthetic_only: true, funds_status: "NONCASH_ONLY",
      });
      if (url.endsWith("/processor/programs/")) return response({
        programs: [], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY",
      });
      if (url.endsWith("/correct/")) return response({ application: resubmitted, changed: true });
      if (url.includes("/family/applications/")) return response({ application: requested });
      throw new Error("unexpected endpoint " + url);
    });
    render(<JirehSGOIntakePage />);
    expect(await screen.findByRole("button", { name: "Save correction and resubmit" })).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Correct or confirm fictional grade"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Save correction and resubmit" }));
    expect(await screen.findByText(/Correction not confirmed/)).toBeTruthy();
    expect(screen.queryByText(/Correction saved, read back and resubmitted/)).toBeNull();
  });
  it("does not claim processor success when the independent queue remains stale", async () => {
    const processor = { id: PID, organization: "Fictional SGO A", name: "Synthetic 2027" };
    getAccessToken.mockReturnValue("processor-session-a");
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) return response({
        programs: [], synthetic_only: true, funds_status: "NONCASH_ONLY",
      });
      if (url.endsWith("/processor/programs/")) return response({
        programs: [processor], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY",
      });
      if (url.endsWith("/queue/")) return response({
        applications: [saved], program_id: PID, authority: "PROCESSOR_VERIFICATION_ONLY",
      });
      if (url.endsWith("/request-correction/")) return response({
        application: { ...saved, status: "CORRECTION_REQUESTED", revision: 2,
          correction_reason: "GRADE_UNVERIFIED" }, changed: true,
      });
      throw new Error("unexpected endpoint " + url);
    });
    render(<JirehSGOIntakePage />);
    fireEvent.click(await screen.findByRole("button", { name: "Request correction" }));
    expect(await screen.findByText(/Correction request not confirmed/)).toBeTruthy();
    expect(screen.queryByText(/Nonbinding verification correction request recorded and read back/)).toBeNull();
  });
  it.each([false, true])("records a delegated correction request without any award workflow (hosted=%s)", async (hosted) => {
    vi.stubEnv("VITE_LOCAL_DEMO", hosted ? "0" : "1");
    vi.stubEnv("VITE_HOSTED_JIREH_DEMO", hosted ? "1" : "0");
    let status = "SUBMITTED";
    getAccessToken.mockReturnValue("processor-session-a");
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) {
        if (hosted) throw Object.assign(new Error("Not found"), { status: 404 });
        return response({ programs: [], synthetic_only: true, funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/processor/programs/")) {
        return response({ programs: [{
          id: PID, organization: "Fictional SGO A", name: "Synthetic 2027",
        }], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/request-correction/")) {
        status = "CORRECTION_REQUESTED";
        return response({ application: { ...saved, revision: 2, status, correction_reason: "GRADE_UNVERIFIED" }, changed: true });
      }
      if (url.endsWith("/queue/")) return response({
        applications: [{ ...saved, revision: status === "SUBMITTED" ? 1 : 2, status,
          correction_reason: status === "CORRECTION_REQUESTED" ? "GRADE_UNVERIFIED" : null }],
        program_id: PID, authority: "PROCESSOR_VERIFICATION_ONLY",
      });
      throw new Error("unexpected fictional endpoint " + url);
    });
    render(<JirehSGOIntakePage />);
    const button = await screen.findByRole("button", { name: "Request correction" });
    fireEvent.click(button);
    await waitFor(() => expect(authenticatedFetch.mock.calls.some(
      ([url, opts]) => url.endsWith("/request-correction/")
        && opts.method === "POST" && JSON.parse(opts.body).reason === "GRADE_UNVERIFIED",
    )).toBe(true));
    expect(await screen.findByText(/Nonbinding verification correction request recorded/)).toBeTruthy();
    expect(screen.getByText(/No award, eligibility determination, or disbursement authority/)).toBeTruthy();
  });
});

describe("Hosted SGO refusal", () => {
  it.each([403, 500])("refuses partial grants when counterpart returns HTTP %s", async (status) => {
    vi.stubEnv("VITE_LOCAL_DEMO", "0");
    vi.stubEnv("VITE_HOSTED_JIREH_DEMO", "1");
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) return response({ programs: [FAMILY], synthetic_only: true, funds_status: "NONCASH_ONLY" });
      throw Object.assign(new Error("Denied"), { status });
    });
    render(<JirehSGOIntakePage />);
    expect(await screen.findByText("Fictional partner-program access could not be verified.")).toBeTruthy();
    expect(screen.queryByLabelText("Partner SGO and program")).toBeNull();
  });
  it.each([403, 404, 500])("does not authorize intake after HTTP %s", async (status) => {
    vi.stubEnv("VITE_LOCAL_DEMO", "0");
    vi.stubEnv("VITE_HOSTED_JIREH_DEMO", "1");
    authenticatedFetch.mockRejectedValue(Object.assign(new Error("Denied"), { status }));
    render(<JirehSGOIntakePage />);
    expect(await screen.findByText("Fictional partner-program access could not be verified.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Submit fictional application" })).toBeNull();
    expect(screen.queryByLabelText("Partner SGO and program")).toBeNull();
  });
});
