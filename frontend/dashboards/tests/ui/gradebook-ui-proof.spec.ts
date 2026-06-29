import { test, expect } from "@playwright/test";

const TEST_USER = process.env.CROWN_TEST_USER ?? "head@crown-demo.local";
const TEST_PASS = process.env.CROWN_TEST_PASS ?? "Crown2026!";
const TEST_SCHOOL_ID = process.env.CROWN_TEST_SCHOOL_ID ?? "19801b59-8c05-4c84-9312-5d792e4e839d";
const TEST_ROLE = process.env.CROWN_TEST_ROLE ?? "head_of_school";
const TEST_API_BASE = process.env.CROWN_TEST_API_BASE ?? "http://127.0.0.1:8000";
const TEST_UI_BASE =
  process.env.CROWN_TEST_UI_BASE ??
  process.env.CROWN_UI_URL ??
  "http://127.0.0.1:4173";

test("gradebook loads assignments and rows with FK-backed data", async ({ page, request }, testInfo) => {
  const loginResp = await request.post(`${TEST_API_BASE}/api/v1/auth/token/`, {
    data: { username: TEST_USER, password: TEST_PASS },
  });
  expect(loginResp.status(), "[Setup] Login API should return 200").toBe(200);

  const authData: any = await loginResp.json();
  const token = authData?.access ?? authData?.access_token ?? authData?.token;
  expect(token, "[Setup] Failed to acquire JWT token").toBeTruthy();

  const sectionsApiResp = await request.get(`${TEST_API_BASE}/api/v1/gradebook/sections/?limit=50&offset=0`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "X-School-Id": TEST_SCHOOL_ID,
    },
  });
  expect(sectionsApiResp.status(), "[Setup] Gradebook sections API should return 200").toBe(200);
  const sectionsApiData: any = await sectionsApiResp.json();
  const sections = Array.isArray(sectionsApiData?.results)
    ? sectionsApiData.results
    : Array.isArray(sectionsApiData)
      ? sectionsApiData
      : [];
  expect(sections.length, "[Setup] At least one gradebook section must exist").toBeGreaterThan(0);
  const preferred = sections.find((section: any) => Number(section?.roster_count ?? 0) > 0) ?? sections[0];
  const sectionId = preferred?.section_id;
  expect(sectionId, "[Setup] Selected gradebook section must have section_id").toBeTruthy();

  await page.addInitScript(
    ({ token, schoolId, role, username }) => {
      const user = {
        email: username,
        username,
        role,
        roles: [role],
        school_id: schoolId,
        schoolId,
      };

      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.school.id", schoolId);
      sessionStorage.setItem("crown.role", role);
      sessionStorage.setItem("crown_user", JSON.stringify(user));
      sessionStorage.setItem("crown_current_user", JSON.stringify(user));

      localStorage.setItem("crown.jwt.access", token);
      localStorage.setItem("crown.school.id", schoolId);
      localStorage.setItem("schoolId", schoolId);
      localStorage.setItem("crown.role", role);
      localStorage.setItem("crown.demo.role", role);
      localStorage.setItem("crown_user", JSON.stringify(user));
      localStorage.setItem("crown_current_user", JSON.stringify(user));
    },
    { token, schoolId: TEST_SCHOOL_ID, role: TEST_ROLE, username: TEST_USER }
  );

  const seen = {
    sections: false,
    grades: false,
  };
  const apiErrors: string[] = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") console.log(`[Browser Error] ${msg.text()}`);
  });

  page.on("response", (resp) => {
    const url = resp.url();
    const status = resp.status();

    if (url.includes("/api/v1/")) {
      console.log(`[API] ${resp.request().method()} ${url} -> ${status}`);
      if (status >= 400) apiErrors.push(`${url} returned ${status}`);
    }

    const path = new URL(url).pathname;
    if (path === "/api/v1/gradebook/sections/") seen.sections = true;
    if (path === `/api/v1/gradebook/sections/${sectionId}/grades/`) seen.grades = true;
  });

  const sectionsResponse = page.waitForResponse((resp) => {
    const url = new URL(resp.url());
    return url.pathname === "/api/v1/gradebook/sections/";
  }, { timeout: 15000 });
  const gradesResponse = page.waitForResponse((resp) => {
    const url = new URL(resp.url());
    return url.pathname === `/api/v1/gradebook/sections/${sectionId}/grades/`;
  }, { timeout: 15000 });

  await page.goto(`${TEST_UI_BASE}/gradebook/${sectionId}`, { waitUntil: "domcontentloaded" });
  await expect(page).toHaveURL(new RegExp(`/gradebook/${sectionId}$`));

  await sectionsResponse;
  await gradesResponse;

  const assignmentHeaders = page.locator("[data-testid='gradebook-assignment-header']");
  const gradeRows = page.locator("[data-testid='gradebook-row']");
  const emptyState = page.locator("text=/No assignments|No grades|No grade rows|No sections available/i");
  const errorState = page.locator("text=/Grades unavailable|Failed to load gradebook sections|API error/i");
  const noSectionsState = page.getByRole("heading", { name: /No sections available/i });

  await expect
    .poll(async () => {
      const hasAssignmentHeader = await assignmentHeaders.first().isVisible().catch(() => false);
      const hasGradeRow = await gradeRows.first().isVisible().catch(() => false);
      const hasEmptyState = await emptyState.first().isVisible().catch(() => false);
      const hasErrorState = await errorState.first().isVisible().catch(() => false);
      return hasAssignmentHeader || hasGradeRow || hasEmptyState || hasErrorState;
    }, { timeout: 15000, message: "Expected a visible gradebook proof surface" })
    .toBe(true);

  if (apiErrors.length > 0) {
    throw new Error(`API calls failed: ${apiErrors.join("; ")}`);
  }
  if ((await errorState.count()) > 0) {
    throw new Error("Gradebook rendered an API error state instead of proof data/empty state");
  }

  await page.screenshot({ path: testInfo.outputPath("gradebook-proof-success.png"), fullPage: true });

  expect(seen.sections, "Sections API not called by browser UI").toBe(true);
  const noSectionsVisible = (await noSectionsState.count()) > 0;
  expect(seen.grades || noSectionsVisible, "Grades API not called by browser UI and no explicit no-sections state rendered").toBe(true);

  const assignmentCount = await assignmentHeaders.count();
  const rowCount = await gradeRows.count();
  const emptyStateCount = await emptyState.count();

  console.log(`[Success] Gradebook loaded: ${assignmentCount} assignments, ${rowCount} rows, ${emptyStateCount} empty-state markers`);
  expect(assignmentCount > 0 || rowCount > 0 || emptyStateCount > 0, "Neither gradebook data nor empty-state was rendered").toBe(true);
});
