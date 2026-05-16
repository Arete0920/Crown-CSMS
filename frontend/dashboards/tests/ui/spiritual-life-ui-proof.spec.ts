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

  test("spiritual life dashboard renders the expected command center", async ({ page }) => {
    await seedDemoSession(page, "spiritual_life");
    await page.goto(BASE + "/spiritual-life", { waitUntil: "networkidle" });

    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("body")).toContainText(/Good morning, Chaplain!/i);
    await expect(page.locator("body")).toContainText(/Chapel Attendance/i);
    await expect(page.locator("body")).toContainText(/Service Hours/i);
    await expect(page.locator("body")).toContainText(/Pastoral priorities/i);
    await expect(page.locator("a[href='/spiritual-life']").first()).toBeVisible();
    await expect(page.locator("a[href='/service-hours']").first()).toBeVisible();
  });
});
