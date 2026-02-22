import { test, expect } from "@playwright/test";

const TEST_USER = process.env.CROWN_TEST_USER ?? "teacher";
const TEST_PASS = process.env.CROWN_TEST_PASS ?? "Crown2026!";
const TEST_SCHOOL_ID = process.env.CROWN_TEST_SCHOOL_ID ?? "19801b59-8c05-4c84-9312-5d792e4e839d";
const TEST_API_BASE = process.env.CROWN_TEST_API_BASE ?? "http://127.0.0.1:8000";
const TEST_UI_BASE = process.env.CROWN_TEST_UI_BASE ?? "http://localhost:3000";

test("gradebook loads assignments and rows with FK-backed data", async ({ page, request }) => {
  // Step 1: Acquire JWT via API
  const loginResp = await request.post(`${TEST_API_BASE}/api/v1/auth/token/`, {
    data: { username: TEST_USER, password: TEST_PASS },
  });
  const authData: any = await loginResp.json();
  const token = authData?.access ?? authData?.token;
  expect(token, "[Setup] Failed to acquire JWT token").toBeTruthy();

  // Step 2: Inject JWT + school ID into sessionStorage + localStorage before page load
  // (Ensures authenticatedFetch() can read tenant header for X-School-Id enforcement)
  await page.addInitScript(
    ({ token, schoolId }) => {
      // Session storage (primary)
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.school.id", schoolId);

      // Local storage (backup fallback for authClient.js)
      localStorage.setItem("crown.jwt.access", token);
      localStorage.setItem("crown.school.id", schoolId);
    },
    { token, schoolId: TEST_SCHOOL_ID }
  );

  // Step 3: Track API calls and log errors
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
    
    // Log all /api/v1/ responses for diagnostics
    if (url.includes("/api/v1/")) {
      console.log(`[API] ${resp.request().method()} ${url} → ${status}`);
      if (status >= 400) {
        apiErrors.push(`${url} returned ${status}`);
      }
    }
    
    if (url.includes("/gradebook/sections") && !url.includes("/grades")) seen.sections = true;
    if (url.includes("/gradebook/sections/") && url.includes("/grades")) seen.grades = true;
  });

  // Step 4: Navigate directly to gradebook (token is already injected)
  await page.goto(`${TEST_UI_BASE}/gradebook`, { waitUntil: "domcontentloaded" });

  // Step 4.5: Wait for page to auto-select first section and load grades (with extra time)
  await page.waitForTimeout(2000);

  // Early diagnostic: check if any API errors occurred before checking elements
  if (apiErrors.length > 0) {
    console.log(`[ERROR] API failures detected: ${apiErrors.join(", ")}`);
    throw new Error(`API calls failed: ${apiErrors.join("; ")}`);
  }

  // Step 5: Wait for assignment headers to render
  const firstAssignmentHeader = page.locator("[data-testid='gradebook-assignment-header']").first();
  await expect(firstAssignmentHeader).toBeVisible({ timeout: 15000 });

  // Step 6: Wait for at least one grade row to render
  const firstRow = page.locator("[data-testid='gradebook-row']").first();
  await expect(firstRow).toBeVisible({ timeout: 10000 });

  // Step 7: Capture screenshot for debugging
  await page.screenshot({ path: "gradebook-proof-success.png", fullPage: true });

  // Step 8: Verify API calls were made
  expect(seen.sections, "Sections API not called").toBe(true);
  expect(seen.grades, "Gradebook grades API not called").toBe(true);

  // Step 9: Verify data is populated (optional but visible in DOM)
  const assignmentCount = await page.locator("[data-testid='gradebook-assignment-header']").count();
  const rowCount = await page.locator("[data-testid='gradebook-row']").count();
  
  console.log(`[Success] Gradebook loaded: ${assignmentCount} assignments, ${rowCount} rows`);
  expect(assignmentCount, "No assignments rendered").toBeGreaterThan(0);
  expect(rowCount, "No grade rows rendered").toBeGreaterThan(0);
});
