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
  it("submits explicitly consented application and shows persisted readback", async () => {
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) {
        return response({ programs: [FAMILY], synthetic_only: true, funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/processor/programs/")) {
        return response({ programs: [], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/family/submit/")) return response({ application: saved, created: true });
      if (url.includes("/family/applications/")) return response({ application: saved });
      throw new Error("unexpected fictional endpoint: " + url);
    });
    render(<JirehSGOIntakePage />);
    expect(await screen.findByLabelText("Partner SGO and program")).toBeTruthy();
    const submit = screen.getByRole("button", { name: "Submit fictional application" });
    expect(submit.disabled).toBe(true);
    fireEvent.click(screen.getByRole("checkbox"));
    expect(submit.disabled).toBe(false);
    fireEvent.click(submit);
    await waitFor(() => expect(authenticatedFetch.mock.calls.some(
      ([url, opts]) => url.endsWith("/family/submit/") && opts.method === "POST"
        && opts.omitSchoolContext === true
        && JSON.parse(opts.body).consent_version === "DEMO_CONSENT_V1",
    )).toBe(true));
    expect(await screen.findByText(/Persistent application readback/)).toBeTruthy();
    expect(screen.getByText(/Status:/).textContent).toContain("SUBMITTED");
    expect(screen.getByText(/Status:/).textContent).toContain("revision: 1");
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

  it("records a delegated correction request without any award workflow", async () => {
    let status = "SUBMITTED";
    getAccessToken.mockReturnValue("processor-session-a");
    authenticatedFetch.mockImplementation(async (url) => {
      if (url.endsWith("/family/programs/")) {
        return response({ programs: [], synthetic_only: true, funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/processor/programs/")) {
        return response({ programs: [{
          id: PID, organization: "Fictional SGO A", name: "Synthetic 2027",
        }], authority: "PROCESSOR_VERIFICATION_ONLY", funds_status: "NONCASH_ONLY" });
      }
      if (url.endsWith("/request-correction/")) {
        status = "CORRECTION_REQUESTED";
        return response({ application: { ...saved, revision: 2, status }, changed: true });
      }
      if (url.endsWith("/queue/")) return response({
        applications: [{ ...saved, revision: status === "SUBMITTED" ? 1 : 2, status }],
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
