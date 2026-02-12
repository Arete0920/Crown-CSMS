import { test, expect } from "@playwright/test";

const BASE_URL = process.env.CROWN_UI_URL ?? "http://localhost:3000";
const API_BASE = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

const USERNAME = "head@crown-demo.local";
const PASSWORD = "demo1234";
const SCHOOL_ID = "b45b8c5a-6708-4597-aad9-a226627b2962";

test("UI proof: Academics → Roster → Load gradebook → Load assignments (200s)", async ({ page, request }) => {
  // Fetch section ID dynamically (same pattern as API proof)
  const loginData = { username: USERNAME, password: PASSWORD };
  const loginResp = await request.post(`${API_BASE}/api/v1/auth/token/`, { data: loginData });
  const authData: any = await loginResp.json();
  const authToken = authData?.access ?? authData?.token;

  const sectionsResp = await request.get(`${API_BASE}/api/v1/academics/sections/`, {
    headers: {
      Authorization: `Bearer ${authToken}`,
      "X-School-Id": SCHOOL_ID,
    },
  });
  const sectionsData: any = await sectionsResp.json();
  const sections = sectionsData?.results ?? sectionsData?.data ?? sectionsData ?? [];
  const SECTION_ID = sections[0]?.section_id;
  console.log(`[UI Setup] Using section: ${SECTION_ID}`);

  const seen = {
    roster: [] as Array<{ url: string; status: number }>,
    grades: [] as Array<{ url: string; status: number }>,
    assignments: [] as Array<{ url: string; status: number }>,
  };

  page.on("response", (resp) => {
    const url = resp.url();
    const status = resp.status();

    // Match endpoints for any section (not hard-coded UUID)
    if (url.includes(`/academics/sections/`) && url.includes(`/roster`)) {
      seen.roster.push({ url, status });
    }
    if (url.includes(`/gradebook/sections/`) && url.includes(`/grades`)) {
      seen.grades.push({ url, status });
    }
    if (url.includes(`/gradebook/sections/`) && url.includes(`/assignments`)) {
      seen.assignments.push({ url, status });
    }
  });

  // Login
  await page.goto(BASE_URL, { waitUntil: "domcontentloaded" });

  // Username input (first text input after "Username" label)
  await page.locator("input").first().fill(USERNAME);
  
  // Password input (input[type="password"])
  await page.locator("input[type=password]").fill(PASSWORD);
  
  // School ID input (input with placeholder "UUID...")
  await page.locator('input[placeholder*="UUID"]').fill(SCHOOL_ID);
  
  // Click Login button
  await page.getByRole("button", { name: /^Login$/i }).click();

  await page.waitForTimeout(1000);

  // Navigate directly to gradebook section  
  // Use the SECTION_ID from API fetched earlier
  await page.goto(`${BASE_URL}/gradebook/${SECTION_ID}`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1500);

  // In gradebook read-only view, we can verify the page loaded
  // (roster drawer is in Academics page, not here)
  const pageHeading = page.locator("h1, h2").first();
  await expect(pageHeading).toBeVisible({ timeout: 15000 });

  await page.screenshot({ path: "gb-ui-section-gradebook.png", fullPage: true });

  // In gradebook read-only view, the roster API should be called to show students
  // and assignments/grades APIs populate the grid
  // (No need to click buttons - Gradebook RO auto-loads on mount if section_id is valid)

  // Assertions
  expect(seen.roster.length, `Roster call not observed`).toBeGreaterThan(0);
  expect(seen.grades.length, `Grades call not observed`).toBeGreaterThan(0);
  expect(seen.assignments.length, `Assignments call not observed`).toBeGreaterThan(0);

  expect(seen.roster.some((x) => x.status === 200), `Roster statuses: ${seen.roster.map(x=>x.status).join(",")}`).toBeTruthy();
  expect(seen.grades.some((x) => x.status === 200), `Grades statuses: ${seen.grades.map(x=>x.status).join(",")}`).toBeTruthy();
  expect(seen.assignments.some((x) => x.status === 200), `Assignments statuses: ${seen.assignments.map(x=>x.status).join(",")}`).toBeTruthy();
});
