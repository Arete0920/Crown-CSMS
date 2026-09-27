import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";

const TEST_USER = process.env.CROWN_TEST_USER ?? "teacher";
const TEST_PASS = process.env.CROWN_TEST_PASS;
const TEST_SCHOOL_ID = process.env.CROWN_TEST_SCHOOL_ID ?? "19801b59-8c05-4c84-9312-5d792e4e839d";
const TEST_API_BASE = process.env.CROWN_TEST_API_BASE ?? "http://127.0.0.1:8000";
const TEST_UI_BASE = process.env.CROWN_TEST_UI_BASE ?? "http://localhost:3000";

// Helper: Inject auth into page context for all subsequent navigations
async function injectAuth(page: Page, token: string, schoolId: string) {
  await page.addInitScript(
    ({ token, schoolId }) => {
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.school.id", schoolId);
      localStorage.setItem("crown.jwt.access", token);
      localStorage.setItem("crown.school.id", schoolId);
    },
    { token, schoolId }
  );
}

test("Gradebook Proof: Roster + Grades + Assignments with 200s + auth headers", async ({ page, request }) => {
  if (!TEST_PASS?.trim()) throw new Error("Configure CROWN_TEST_PASS before running this proof.");
  // Step 1: Get an auth token via direct API call (more reliable than UI automation in CI)
  console.log("[Auth] Acquiring JWT token via API...");
  const loginResp = await request.post(`${TEST_API_BASE}/api/v1/auth/token/`, {
    data: { username: TEST_USER, password: TEST_PASS },
  });

  expect(loginResp.status(), "Login API should return 200").toBe(200);
  const authData: any = await loginResp.json();
  const authToken = authData?.access ?? authData?.token;
  expect(authToken, "Token not found in login response").toBeTruthy();
  console.log("[Auth] Token acquired from API");
  console.log("TOKEN_OK=true");

  const schoolId = TEST_SCHOOL_ID;
  console.log("SCHOOL_ID_OK=true\n");

  // Inject auth into page context for future navigations (CRITICAL for UI screenshots)
  await injectAuth(page, authToken, schoolId);
  console.log("[Auth] Injected token + schoolId into page context for future navigations\n");

  // Fetch first available section (resilient to seed variability)
  console.log("[Setup] Fetching available sections from API...");
  const sectionsResp = await page.request.get(`${TEST_API_BASE}/api/v1/academics/sections/`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
      "X-School-Id": TEST_SCHOOL_ID,
    },
  });
  expect(sectionsResp.status(), "Sections API should return 200").toBe(200);
  const sectionsData: any = await sectionsResp.json();
  const sections = sectionsData?.results ?? sectionsData?.data ?? sectionsData ?? [];
  expect(sections.length, "At least one section must exist for proof").toBeGreaterThan(0);
  const SECTION_ID = sections[0].section_id;
  console.log(`[Setup] Using section: ${SECTION_ID}\n`);

  // Step 2: Use the captured token to directly verify the three endpoints
  // (Direct API calls because UI navigation doesn't easily expose all three endpoint triggers)
  console.log(`\n[API Proof] Testing three endpoints with captured token...`);

  const endpoints = [
    {
      name: "Roster",
      url: `${TEST_API_BASE}/api/v1/academics/sections/${SECTION_ID}/roster/`,
      pattern: /roster/i,
    },
    {
      name: "Grades",
      url: `${TEST_API_BASE}/api/v1/gradebook/sections/${SECTION_ID}/grades/`,
      pattern: /grades/i,
    },
    {
      name: "Assignments",
      url: `${TEST_API_BASE}/api/v1/gradebook/sections/${SECTION_ID}/assignments/`,
      pattern: /assignments/i,
    },
  ];

  const results: Array<{ name: string; status: number; pass: boolean }> = [];

  for (const endpoint of endpoints) {
    const response = await page.request.get(endpoint.url, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        "X-School-Id": TEST_SCHOOL_ID,
      },
    });

    const status = response.status();
    const pass = status === 200;

    results.push({
      name: endpoint.name,
      status,
      pass,
    });

    console.log(`  ${endpoint.name}: ${status} ${pass ? "✅" : "❌"}`);
  }

  // Step 3: Take screenshots to document the UI state
  console.log(`\n[UI] Navigating to Academics for roster screenshot...`);
  await page.goto(`${TEST_UI_BASE}/academics`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "gb-ui-section-roster.png", fullPage: true });
  console.log(`  Saved gb-ui-section-roster.png`);

  console.log(`[UI] Navigating to Gradebook for grades grid screenshot...`);
  await page.goto(`${TEST_UI_BASE}/gradebook`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: "gb-ui-gradebook-grid.png", fullPage: true });
  console.log(`  Saved gb-ui-gradebook-grid.png`);

  // Step 4: Validate results
  console.log(`\n[Results Summary]`);
  results.forEach((r) => {
    console.log(`  ${r.name}: HTTP ${r.status} ${r.pass ? "✅ PASS" : "❌ FAIL"}`);
  });

  const allPass = results.every((r) => r.pass && r.status === 200);

  expect(results[0].pass, `Roster endpoint returned ${results[0].status}, expected 200`).toBe(true);
  expect(results[1].pass, `Grades endpoint returned ${results[1].status}, expected 200`).toBe(true);
  expect(results[2].pass, `Assignments endpoint returned ${results[2].status}, expected 200`).toBe(true);

  // Validate that requests were sent with required headers
  // (HTTP 200 response proves the backend accepted the Authorization + X-School-Id headers)
  console.log(`\n[Headers Proof]`);
  console.log(`  Each request was sent with:`);
  console.log(`    - Authorization: Bearer [token]`);
  console.log(`    - X-School-Id: ${schoolId}`);
  console.log(`  All 200 responses prove headers were accepted by backend. ✅`);

  console.log(`\n✅ PASS: All three endpoints returned 200 with required auth headers.`);
});
