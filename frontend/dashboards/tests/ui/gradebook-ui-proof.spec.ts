import { test, expect } from "@playwright/test";

const BASE_URL = process.env.CROWN_UI_URL ?? "http://localhost:3000";
const API_BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

const USERNAME = "head@crown-demo.local";
const PASSWORD = "demo1234";
const SCHOOL_ID = "b45b8c5a-6708-4597-aad9-a226627b2962";

test("gradebook loads assignments and rows with FK-backed data", async ({ page, request }) => {
  // Step 1: Acquire JWT via API
  const loginResp = await request.post(`${API_BASE}/api/v1/auth/token/`, {
    data: { username: USERNAME, password: PASSWORD },
  });
  const authData: any = await loginResp.json();
  const token = authData?.access ?? authData?.token;
  expect(token, "[Setup] Failed to acquire JWT token").toBeTruthy();

  // Step 2: Inject JWT + school ID into sessionStorage before page load
  await page.addInitScript(
    ([jwt, school]) => {
      sessionStorage.setItem("crown.jwt.access", jwt);
      sessionStorage.setItem("crown.school.id", school);
    },
    [token, SCHOOL_ID]
  );

  // Step 3: Track API calls
  const seen = {
    sections: false,
    grades: false,
  };

  page.on("response", (resp) => {
    const url = resp.url();
    if (url.includes("/gradebook/sections") && !url.includes("/grades")) seen.sections = true;
    if (url.includes("/gradebook/sections/") && url.includes("/grades")) seen.grades = true;
  });

  // Step 4: Navigate directly to gradebook (token is already injected)
  await page.goto(`${BASE_URL}/gradebook`, { waitUntil: "domcontentloaded" });

  // Step 5: Wait for assignment headers to render
  const firstAssignmentHeader = page.locator("[data-testid='gradebook-assignment-header']").first();
  await expect(firstAssignmentHeader).toBeVisible({ timeout: 10000 });

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
