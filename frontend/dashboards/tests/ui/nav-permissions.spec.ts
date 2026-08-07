// frontend/dashboards/tests/ui/nav-permissions.spec.ts
//
// Playwright seatbelt: proves sidebar is permission-derived.
// The frontend fetches /api/v1/nav/ and must never broaden the role-scoped
// response or fail open when that service is unavailable.
//
// Session setup: seed sessionStorage with role + schoolId so the frontend
// sends the correct X-School-Id header to /api/v1/nav/.

import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:3000";
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";

async function seedSession(page, role: string) {
  await page.addInitScript(
    ({ role, token, schoolId }) => {
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.role", role);
      sessionStorage.setItem("crown.school.id", schoolId);
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID },
  );
}

test.describe("Nav is permission-derived — sidebar reflects role, not all links", () => {
  test("parent does NOT see Finance, Admissions, Billing, or System Integrity", async ({ page }) => {
    await seedSession(page, "parent");
    await page.goto(`${BASE}/parent`);
    await page.waitForTimeout(1500);

    await expect(page.locator('aside a[href="/finance"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/admissions"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/billing"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/integrity"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/admin"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/board"]')).toHaveCount(0);
  });

  test("teacher does NOT see Finance, Billing, Board, or Admin", async ({ page }) => {
    await seedSession(page, "teacher");
    await page.goto(`${BASE}/teacher`);
    await page.waitForTimeout(1500);

    await expect(page.locator('aside a[href="/finance"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/billing"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/board"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/admin"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/integrity"]')).toHaveCount(0);
  });

  test("CrownLayout fails closed when nav API is unavailable", async ({ page }) => {
    await page.route("**/api/v1/nav/**", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "nav unavailable" }),
      }),
    );

    await seedSession(page, "parent");
    await page.goto(`${BASE}/wizards`);
    await page.waitForTimeout(1000);

    await expect(page.locator("aside.crown-sidebar a")).toHaveCount(0);
    await expect(page.getByText("Role-scoped navigation is temporarily unavailable.", { exact: true })).toBeVisible();
    await expect(page.locator('aside a[href="/finance"]')).toHaveCount(0);
    await expect(page.locator('aside a[href="/admin"]')).toHaveCount(0);
  });

  test("CrownLayout preserves exactly the permission-derived nav response", async ({ page }) => {
    await page.route("**/api/v1/nav/**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          groups: [
            {
              title: "Family",
              items: [{ label: "Parent Home", href: "/parent" }],
            },
          ],
        }),
      }),
    );

    await seedSession(page, "parent");
    await page.goto(`${BASE}/wizards`);

    const aside = page.locator("aside.crown-sidebar");
    await expect(aside).toBeVisible();
    await expect(aside.getByText("Family", { exact: true })).toBeVisible();
    await expect(aside.locator('a[href="/parent"]')).toBeVisible();
    await expect(aside.locator("a")).toHaveCount(1);
    await expect(aside.locator('a[href="/finance"]')).toHaveCount(0);
    await expect(aside.locator('a[href="/admin"]')).toHaveCount(0);
    await expect(aside.locator('a[href="/board"]')).toHaveCount(0);
  });
});
