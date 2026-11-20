// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { apiFetch } from "../lib/api";
import ParentFinancialAidPreparationPage from "./ParentFinancialAidPreparationPage.jsx";
import { setAccessToken, setSelectedSchoolId } from "../utils/authClient";

vi.mock("../lib/api", () => ({ apiFetch: vi.fn() }));
vi.mock("../features/parentJourney/ParentJourneyOverviewPage.jsx", () => ({
  default: () => null,
}));

const YEAR = "11111111-1111-4111-8111-111111111111";
const STUDENT = "22222222-2222-4222-8222-222222222222";
const APPLICATION = "33333333-3333-4333-8333-333333333333";

function snapshot(applications = []) {
  return {
    demo_only: true,
    household_name: "Fictional Family",
    academic_years: [{ id: YEAR, name: "2026-2027" }],
    students: [{ id: STUDENT, name: "Sample Learner" }],
    scenarios: [{ id: "fictional_modest", label: "Invented resources" }],
    applications,
  };
}

const saved = {
  id: APPLICATION,
  academic_year_id: YEAR,
  academic_year_name: "2026-2027",
  status: "SUBMITTED",
  submitted_at: "2026-11-02T15:00:00Z",
  student_ids: [STUDENT],
  awards: [],
};

function jsonResponse(payload) {
  return { json: async () => payload };
}

function arrange(readback) {
  let reads = 0;
  apiFetch.mockImplementation(async (_path, options = {}) => {
    if (options.method === "POST") {
      return jsonResponse({ demo_only: true, application: saved });
    }
    reads += 1;
    return jsonResponse(reads === 1 ? snapshot() : readback);
  });
}

async function submitFictionalApplication() {
  render(<ParentFinancialAidPreparationPage />);
  const submit = await screen.findByRole("button", {
    name: "Submit fictional Financial Aid application",
  });
  await waitFor(() => expect(submit.disabled).toBe(true));
  fireEvent.click(screen.getByRole("checkbox", {
    name: /I confirm all application information is fictional/i,
  }));
  expect(submit.disabled).toBe(false);
  fireEvent.click(submit);
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubEnv("VITE_LOCAL_DEMO", "1");
  setAccessToken("fictional-parent-A");
  setSelectedSchoolId(YEAR);
});
afterEach(() => {
  cleanup();
  sessionStorage.removeItem("crown.website.presenter");
  setAccessToken("");
  setSelectedSchoolId("");
  vi.unstubAllEnvs();
});

describe("Fictional parent Financial Aid saved-record truth", () => {
  it("uses the shared role-scoped CROWN parent shell without exposing administration", async () => {
    arrange(snapshot());
    render(<ParentFinancialAidPreparationPage />);
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeTruthy();
    expect(screen.getByRole("main")).toBeTruthy();
    expect(screen.getByTestId("jireh-family-demo").tagName).toBe("SECTION");
    expect(screen.queryByRole("link", { name: "Platform Control" })).toBeNull();
  });

  it("does not expose local fictional intake outside the explicit local demo build", () => {
    vi.stubEnv("VITE_LOCAL_DEMO", "0");
    render(<ParentFinancialAidPreparationPage />);
    expect(screen.queryByTestId("jireh-family-demo")).toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("confirms submission only after matching canonical authenticated GET readback", async () => {
    arrange(snapshot([saved]));
    await submitFictionalApplication();
    const message = await screen.findByTestId("jireh-submit-confirmation");
    expect(message.textContent).toContain(APPLICATION);
    expect(message.textContent).toContain("independently verified");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(apiFetch.mock.calls.map(([, options]) => options?.method || "GET")).toEqual([
      "GET", "POST", "GET",
    ]);
  });

  it("does not claim success when the server GET is missing the submitted application", async () => {
    arrange(snapshot());
    await submitFictionalApplication();
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "may have been accepted",
      );
    });
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
    expect(apiFetch.mock.calls.filter(([, options]) => options?.method === "POST")).toHaveLength(1);
  });

  it("does not claim success when a submitted application is still a draft on GET", async () => {
    arrange(snapshot([{ ...saved, status: "DRAFT" }]));
    await submitFictionalApplication();
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "may have been accepted",
      );
    });
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
    expect(apiFetch.mock.calls.filter(([, options]) => options?.method === "POST")).toHaveLength(1);
  });

  it("does not claim success when the readback has a foreign student reference", async () => {
    arrange(snapshot([{ ...saved, student_ids: ["44444444-4444-4444-8444-444444444444"] }]));
    await submitFictionalApplication();
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "may have been accepted",
      );
    });
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
    expect(apiFetch.mock.calls.filter(([, options]) => options?.method === "POST")).toHaveLength(1);
  });
  it("drops an old-school GET resolving after a school context switch", async () => {
    let resolveOld;
    const oldResponse = new Promise((resolve) => { resolveOld = resolve; });
    const newSchool = "99999999-9999-4999-8999-999999999999";
    const newSnapshot = {
      ...snapshot(),
      household_name: "Different Fictional Family",
      students: [{ id: "88888888-8888-4888-8888-888888888888", name: "New School Student" }],
    };
    let requests = 0;
    apiFetch.mockImplementation(() => {
      requests += 1;
      return requests === 1 ? oldResponse : Promise.resolve(jsonResponse(newSnapshot));
    });
    render(<ParentFinancialAidPreparationPage />);
    await waitFor(() => expect(requests).toBe(1));
    setSelectedSchoolId(newSchool);
    await screen.findByText("Different Fictional Family");
    resolveOld(jsonResponse({ ...snapshot(), household_name: "Old School Household" }));
    await waitFor(() => expect(requests).toBe(2));
    expect(screen.queryByText("Old School Household")).toBeNull();
    expect(screen.queryByText("Different Fictional Family")).not.toBeNull();
  });

  it("discards a pending POST and clears old-family state when principal rotates", async () => {
    let resolveWrite;
    const write = new Promise((resolve) => { resolveWrite = resolve; });
    let gets = 0;
    let posts = 0;
    apiFetch.mockImplementation((_path, options = {}) => {
      if (options.method === "POST") { posts += 1; return write; }
      gets += 1;
      return Promise.resolve(jsonResponse(gets === 1 ? snapshot() : {
        ...snapshot(), household_name: "Rotated Family",
      }));
    });
    await submitFictionalApplication();
    await waitFor(() => expect(posts).toBe(1));
    setAccessToken("different-fictional-parent");
    // Older main lacks a token-change event. The #612 auth contract publishes
    // this event and this component listens to it without changing authClient.
    window.dispatchEvent(new Event("crown:auth-context-changed"));
    await screen.findByText("Rotated Family");
    resolveWrite(jsonResponse({ demo_only: true, application: saved }));
    await waitFor(() => expect(gets).toBe(2));
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
    expect(screen.queryByText("Fictional Family")).toBeNull();
    expect(posts).toBe(1);
  });

  it("shows a write-uncertain state and blocks duplicate POST when GET fails after 201", async () => {
    let requests = 0;
    let posts = 0;
    apiFetch.mockImplementation((_path, options = {}) => {
      if (options.method === "POST") {
        posts += 1;
        return Promise.resolve(jsonResponse({ demo_only: true, application: saved }));
      }
      requests += 1;
      return requests === 1
        ? Promise.resolve(jsonResponse(snapshot()))
        : Promise.reject(new Error("HTTP 503 unavailable"));
    });
    await submitFictionalApplication();
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain(
      "may have been accepted"
    ));
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
    expect(screen.getByRole("button", { name: "Submit fictional Financial Aid application" }).disabled).toBe(true);
    expect(posts).toBe(1);
  });

  it("blocks a repeated POST when the initial write response is lost", async () => {
    let posts = 0;
    apiFetch.mockImplementation((_path, options = {}) => {
      if (options.method === "POST") {
        posts += 1;
        return Promise.reject(new Error("Network disconnected after request"));
      }
      return Promise.resolve(jsonResponse(snapshot()));
    });
    await submitFictionalApplication();
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain(
      "may have been accepted"
    ));
    expect(screen.getByRole("button", { name: "Submit fictional Financial Aid application" }).disabled).toBe(true);
    expect(posts).toBe(1);
  });

  it("never presents a saved confirmation after identity rotates during GET readback", async () => {
    let resolveReadback;
    const readback = new Promise((resolve) => { resolveReadback = resolve; });
    let gets = 0;
    let posts = 0;
    apiFetch.mockImplementation((_path, options = {}) => {
      if (options.method === "POST") {
        posts += 1;
        return Promise.resolve(jsonResponse({ demo_only: true, application: saved }));
      }
      gets += 1;
      return gets === 1
        ? Promise.resolve(jsonResponse(snapshot()))
        : gets === 2 ? readback
        : Promise.resolve(jsonResponse({ ...snapshot(), household_name: "Switched Family" }));
    });
    await submitFictionalApplication();
    await waitFor(() => expect(gets).toBe(2));
    setSelectedSchoolId("77777777-7777-4777-8777-777777777777");
    await screen.findByText("Switched Family");
    resolveReadback(jsonResponse(snapshot([saved])));
    await waitFor(() => expect(gets).toBe(3));
    expect(screen.queryByTestId("jireh-submit-confirmation")).toBeNull();
    expect(posts).toBe(1);
  });

});

describe("Explicit hosted fictional Aid", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_LOCAL_DEMO", "0");
    vi.stubEnv("VITE_HOSTED_JIREH_DEMO", "1");
  });
  function hostedSnapshot(applications = []) {
    return { ...snapshot(), household_name: undefined, household: "Fictional Family", synthetic_only: true,
      applications: applications.map((app) => ({ id: app.id, status: app.status,
        academic_year_id: app.academic_year_id, student_ids: app.student_ids, submitted_at: app.submitted_at })),
    };
  }
  it("submits to guarded hosted API, independently reads and survives remount", async () => {
    let stored = false;
    apiFetch.mockImplementation(async (path, options = {}) => {
      expect(path).toBe("/api/v1/buyer-demo/jireh/aid/family/");
      if (options.method === "POST") {
        stored = true;
        return jsonResponse({ demo_only: true, application: saved });
      }
      return jsonResponse(hostedSnapshot(stored ? [saved] : []));
    });
    await submitFictionalApplication();
    expect((await screen.findByTestId("jireh-submit-confirmation")).textContent).toContain("independently verified");
    expect(apiFetch.mock.calls.map(([, opts]) => opts?.method || "GET")).toEqual(["GET", "POST", "GET"]);
    expect(screen.queryByText(/Offered-award records:/)).toBeNull();
    cleanup();
    render(<ParentFinancialAidPreparationPage />);
    expect(await screen.findByText(/Duplicate submission is disabled/)).toBeTruthy();
    expect(screen.getByText("Fictional Family")).toBeTruthy();
  });
  it("refuses hosted readback missing the synthetic-only contract", async () => {
    apiFetch.mockResolvedValue(jsonResponse({ ...hostedSnapshot(), synthetic_only: false }));
    render(<ParentFinancialAidPreparationPage />);
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Submit fictional Financial Aid application" })).toBeNull();
  });
});


it("uses the reserved presenter realm with the normal build and scoped synthetic readback", async () => {
  vi.stubEnv("VITE_LOCAL_DEMO", "0");
  vi.stubEnv("VITE_HOSTED_JIREH_DEMO", "0");
  setSelectedSchoolId("cd216908-b692-5fa7-997b-743f811f1ea9");
  apiFetch.mockResolvedValue(jsonResponse({ ...snapshot(), synthetic_only: true, household: "Reed Family" }));
  render(<ParentFinancialAidPreparationPage />);
  await screen.findByRole("button", { name: "Submit fictional Financial Aid application" });
  expect(apiFetch).toHaveBeenCalledWith("/api/v1/presenter/jireh/aid/family/");
});

describe("Two-child Reed Jireh presenter status", () => {
  const schoolId = "cd216908-b692-5fa7-997b-743f811f1ea9";
  const avery = "44444444-4444-4444-8444-444444444444";
  const jordan = "55555555-5555-4555-8555-555555555555";
  const students = [
    { id: avery, name: "Avery Reed" },
    { id: jordan, name: "Jordan Reed" },
  ];
  const application = { ...saved, student_ids: [avery, jordan] };
  const family = {
    ...snapshot([application]), synthetic_only: true, household: "Reed Family",
    students,
  };
  const award = {
    id: "66666666-6666-4666-8666-666666666666",
    student_id: avery, academic_year_id: YEAR, aid_application_id: APPLICATION,
    awarded_cents: 25000, decision_status: "ACCEPTED",
  };

  beforeEach(() => {
    vi.stubEnv("VITE_LOCAL_DEMO", "0");
    vi.stubEnv("VITE_HOSTED_JIREH_DEMO", "0");
    setSelectedSchoolId(schoolId);
  });

  it("reads both children's saved award decisions without a second application", async () => {
    apiFetch.mockImplementation(async (path) => {
      if (path === "/api/v1/presenter/jireh/aid/family/") {
        return jsonResponse(family);
      }
      if (path.startsWith("/api/v1/aid/family/status/?")) {
        const params = new URLSearchParams(path.split("?")[1]);
        expect(params.get("academic_year_id")).toBe(YEAR);
        const student = params.get("student_id");
        expect([avery, jordan]).toContain(student);
        return jsonResponse({
          application: { id: APPLICATION },
          awards: student === avery ? [award] : [],
        });
      }
      throw new Error("Unexpected Jireh endpoint: " + path);
    });
    render(<ParentFinancialAidPreparationPage />);
    const panel = await screen.findByTestId("jireh-student-status");
    expect(panel.textContent).not.toContain("No awards, eligibility decisions");
    fireEvent.click(screen.getByRole("button", { name: "Refresh student aid status" }));
    await waitFor(() => expect(panel.textContent).toContain("ACCEPTED"));
    expect(panel.textContent).toContain("Avery Reed");
    expect(panel.textContent).toContain("Jordan Reed");
    expect(panel.textContent).toContain("$250.00");
    expect(panel.textContent).toContain("No award recorded for this student.");
    const urls = apiFetch.mock.calls.map(([path]) => path);
    expect(urls).toHaveLength(3);
    expect(urls.filter((path) => path.startsWith("/api/v1/aid/family/status/?"))).toHaveLength(2);
    expect(apiFetch.mock.calls.every(([, options]) => !options?.method)).toBe(true);
  });

  it("fails closed when a student's award points to a different child", async () => {
    apiFetch.mockImplementation(async (path) => {
      if (path === "/api/v1/presenter/jireh/aid/family/") return jsonResponse(family);
      const params = new URLSearchParams(path.split("?")[1]);
      return jsonResponse({
        application: { id: APPLICATION },
        awards: params.get("student_id") === avery
          ? [{ ...award, student_id: jordan }]
          : [],
      });
    });
    render(<ParentFinancialAidPreparationPage />);
    const panel = await screen.findByTestId("jireh-student-status");
    fireEvent.click(screen.getByRole("button", { name: "Refresh student aid status" }));
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toContain(
        "did not match the verified family application"
      );
    });
    expect(panel.textContent).not.toContain("$250.00");
    expect(panel.textContent).not.toContain("ACCEPTED");
  });
});

describe("Website Jireh Financial Aid guided replay", () => {
  const schoolId = "cd216908-b692-5fa7-997b-743f811f1ea9";
  const avery = "44444444-4444-4444-8444-444444444444";
  const jordan = "55555555-5555-4555-8555-555555555555";
  const students = [{ id: avery, name: "Avery Reed" }, { id: jordan, name: "Jordan Reed" }];
  const application = { ...saved, student_ids: [avery, jordan] };

  beforeEach(() => {
    vi.stubEnv("VITE_LOCAL_DEMO", "0");
    vi.stubEnv("VITE_HOSTED_JIREH_DEMO", "0");
    setSelectedSchoolId(schoolId);
    sessionStorage.setItem("crown.website.presenter", "1");
  });

  it("replays saved family and application in three steps without offering any writes", async () => {
    apiFetch.mockImplementation(async (path) => {
      if (path === "/api/v1/presenter/jireh/aid/family/") {
        return jsonResponse({
          ...snapshot([application]), synthetic_only: true,
          household: "Reed Family", students,
        });
      }
      if (path.startsWith("/api/v1/aid/family/status/?")) {
        const params = new URLSearchParams(path.split("?")[1]);
        return jsonResponse({
          application: { id: APPLICATION },
          awards: params.get("student_id") === avery
            ? [{
                id: "66666666-6666-4666-8666-666666666666",
                student_id: avery, academic_year_id: YEAR,
                aid_application_id: APPLICATION, awarded_cents: 25000,
                decision_status: "ACCEPTED",
              }]
            : [],
        });
      }
      throw new Error("Unexpected endpoint: " + path);
    });
    render(<ParentFinancialAidPreparationPage />);
    const walkthrough = await screen.findByTestId("jireh-website-walkthrough");
    expect(await screen.findByTestId("jireh-website-family")).toBeTruthy();
    expect(walkthrough.textContent).toContain("Jordan Reed");
    expect(walkthrough.textContent).toContain("Avery Reed");
    expect(screen.queryByRole("button", { name: "Submit fictional Financial Aid application" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "2. Saved application" }));
    expect(await screen.findByTestId("jireh-saved-applications")).toBeTruthy();
    expect(screen.queryByText(/Duplicate submission is disabled/)).toBeNull();
    expect(screen.getByText(/Selected applicant students:/).textContent).toContain("Jordan Reed");
    fireEvent.click(screen.getByRole("button", { name: "3. Aid decisions" }));
    const panel = await screen.findByTestId("jireh-student-status");
    fireEvent.click(screen.getByRole("button", { name: "Refresh student aid status" }));
    await waitFor(() => expect(panel.textContent).toContain("ACCEPTED"));
    expect(panel.textContent).toContain("Jordan Reed");
    expect(panel.textContent).toContain("$250.00");
    expect(panel.textContent).toContain("No award recorded for this student.");
    expect(apiFetch.mock.calls.every(([, opts]) => !opts?.method || opts.method === "GET")).toBe(true);
  });

  it("fails closed without a saved case and cannot fabricate a decision", async () => {
    apiFetch.mockResolvedValue(jsonResponse({
      ...snapshot([]), synthetic_only: true, household: "Reed Family", students,
    }));
    render(<ParentFinancialAidPreparationPage />);
    await screen.findByTestId("jireh-website-walkthrough");
    fireEvent.click(screen.getByRole("button", { name: "3. Aid decisions" }));
    expect(await screen.findByText(/No submitted fictional application is available/)).toBeTruthy();
    expect(screen.queryByTestId("jireh-student-status")).toBeNull();
    expect(screen.queryByRole("button", { name: "Submit fictional Financial Aid application" })).toBeNull();
    expect(apiFetch).toHaveBeenCalledTimes(1);
  });
});
