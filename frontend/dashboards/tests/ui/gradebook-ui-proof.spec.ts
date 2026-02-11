import { test, expect } from "@playwright/test";

const BASE_URL = process.env.CROWN_UI_URL ?? "http://localhost:3000";

const USERNAME = "head@crown-demo.local";
const PASSWORD = "Crown2026Demo!";
const SCHOOL_ID = "b45b8c5a-6708-4597-aad9-a226627b2962";

const SECTION_ID = "044882e0-3405-4542-a237-32f1adf4f047";

test("UI proof: Academics → Roster → Load gradebook → Load assignments (200s)", async ({ page }) => {
  const seen = {
    roster: [] as Array<{ url: string; status: number }>,
    grades: [] as Array<{ url: string; status: number }>,
    assignments: [] as Array<{ url: string; status: number }>,
  };

  page.on("response", (resp) => {
    const url = resp.url();
    const status = resp.status();

    // Match your real endpoints (tight patterns)
    if (url.includes(`/academics/sections/${SECTION_ID}/roster`)) {
      seen.roster.push({ url, status });
    }
    if (url.includes(`/gradebook/sections/${SECTION_ID}/grades`)) {
      seen.grades.push({ url, status });
    }
    if (url.includes(`/gradebook/sections/${SECTION_ID}/assignments`)) {
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

  // Academics
  await page.goto(`${BASE_URL}/academics`, { waitUntil: "domcontentloaded" });

  // Open roster drawer for exact section
  await page.getByTestId(`btn-open-roster-${SECTION_ID}`).click();
  await expect(page.getByTestId("roster-drawer")).toBeVisible({ timeout: 15000 });

  await page.screenshot({ path: "gb-ui-section-roster.png", fullPage: true });

  // Click first student to reveal quick links
  const firstStudent = page.locator("ul li").first();
  await expect(firstStudent).toBeVisible({ timeout: 5000 });
  await firstStudent.click();
  await page.waitForTimeout(500);

  // Trigger grades
  await page.getByTestId("btn-load-gradebook").click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: "gb-ui-gradebook-grid.png", fullPage: true });

  // Trigger assignments
  await page.getByTestId("btn-load-assignments").click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: "gb-ui-assignments.png", fullPage: true });

  // Assertions
  expect(seen.roster.length, `Roster call not observed`).toBeGreaterThan(0);
  expect(seen.grades.length, `Grades call not observed`).toBeGreaterThan(0);
  expect(seen.assignments.length, `Assignments call not observed`).toBeGreaterThan(0);

  expect(seen.roster.some((x) => x.status === 200), `Roster statuses: ${seen.roster.map(x=>x.status).join(",")}`).toBeTruthy();
  expect(seen.grades.some((x) => x.status === 200), `Grades statuses: ${seen.grades.map(x=>x.status).join(",")}`).toBeTruthy();
  expect(seen.assignments.some((x) => x.status === 200), `Assignments statuses: ${seen.assignments.map(x=>x.status).join(",")}`).toBeTruthy();
});
