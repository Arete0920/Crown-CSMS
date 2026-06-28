import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
const DEMO_SCHOOL_ID =
  process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";

async function seedDemoSession(page, role: string) {
  await page.addInitScript(
    ({ role, token, schoolId }) => {
      try {
        sessionStorage.setItem("crown.jwt.access", token);
        sessionStorage.setItem("crown.role", role);
        sessionStorage.setItem("crown.school.id", schoolId);
        localStorage.setItem("crown.jwt.access", token);
        localStorage.setItem("crown.role", role);
        localStorage.setItem("crown.school.id", schoolId);
        localStorage.setItem("crown.demo.role", role);
      } catch {
        // ignore
      }
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}

async function installApiStubs(page) {
  await page.route("**/api/v1/nav/", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ groups: [] }),
    });
  });

  await page.route("**/api/v1/**/metrics/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
  });

  await page.route("**/api/v1/**/summary/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) });
  });
}

test.describe("Spiritual Life UI proof", () => {
  test.beforeEach(async ({ page }) => {
    await installApiStubs(page);
  });

  for (const role of ["chaplain", "spiritual_life"]) {
    test(`root redirect resolves ${role} to /spiritual-life`, async ({ page }) => {
      await seedDemoSession(page, role);
      await page.goto(BASE + "/", { waitUntil: "networkidle" });
      await expect(page).toHaveURL((url) => url.pathname === "/spiritual-life");
    });
  }

  test("spiritual life dashboard renders the biblical formation command center", async ({ page }) => {
    await seedDemoSession(page, "spiritual_life");
    await page.goto(BASE + "/spiritual-life", { waitUntil: "networkidle" });

    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("body")).toContainText(/Good morning, Chaplain!/i);
    await expect(page.locator("body")).toContainText(/Spiritual Life & Biblical Formation/i);
    await expect(page.locator("body")).toContainText(/Chapel Attendance/i);
    await expect(page.locator("body")).toContainText(/Daily Devotion Publishing/i);
    await expect(page.locator("body")).toContainText(/Spiritual Counseling & Care/i);
    await expect(page.locator("body")).toContainText(/Biblical Worldview Priorities/i);
    await expect(page.locator("body")).toContainText(/Portrait of the Graduate Alignment/i);
    await expect(page.locator("body")).toContainText(/Church & Pastor Relations/i);
    await expect(page.locator("body")).toContainText(/Christian Education Sundays/i);
    await expect(page.locator("body")).toContainText(/Christian College & Calling Pathways/i);
    await expect(page.locator("body")).toContainText(/Formation Evidence & Reports/i);
    await expect(page.getByRole("link", { name: /Open Microsoft Teams/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Open Outlook/i })).toBeVisible();
    await expect(page.locator("a[href='/spiritual-life']").first()).toBeVisible();
  });
});
