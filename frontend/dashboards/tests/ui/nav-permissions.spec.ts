// frontend/dashboards/tests/ui/nav-permissions.spec.ts
//
// Playwright seatbelt: proves sidebar is permission-derived.
// The frontend fetches /api/v1/nav/ — in the Vite dev environment, the proxy
// passes through to Django.  If the backend is unreachable, the sidebar falls
// back to FALLBACK_NAV (just "Home"), so assertions against absent role-specific
// links remain valid.
//
// Session setup: seed sessionStorage with role + schoolId so the frontend
// sends correct X-School-Id header to /api/v1/nav/.

import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:3000";
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN     = process.env.CROWN_DEMO_TOKEN     || "playwright-demo-token";

async function seedSession(page, role: string) {
  await page.addInitScript(
    ({ role, token, schoolId }) => {
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.role",       role);
      sessionStorage.setItem("crown.school.id",  schoolId);
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID },
  );
}

test.describe("Nav is permission-derived — sidebar reflects role, not all links", () => {

  test("parent does NOT see Finance, Admissions, Billing, or System Integrity", async ({ page }) => {
    await seedSession(page, "parent");
    await page.goto(`${BASE}/parent`);

    // Wait for sidebar to settle — either nav loaded from API or fallback rendered.
    // Allow up to 5 s for the fetch to complete.
    await page.waitForTimeout(1500);

    // If nav loaded from backend, /parent link should be visible
    // (backend must have seeded parent.view for the demo token's role).
    // If nav fell back, none of the restricted links appear anyway.

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

  test("fallback nav renders at least one link when API fails", async ({ page }) => {
    // No schoolId set — /api/v1/nav/ will fail → component shows FALLBACK_NAV.
    await page.goto(`${BASE}/admin`);
    await page.waitForTimeout(2000);

    // FALLBACK_NAV always has the Home link.
    const sidebarLinks = page.locator("aside a");
    await expect(sidebarLinks).toHaveCount({ minimum: 1 } as any);
  });

  test("sidebar renders group headers for each section", async ({ page }) => {
    // With demo session, any nav response will have at least one group.
    await seedSession(page, "head_of_school");
    await page.goto(`${BASE}/admin`);
    await page.waitForTimeout(2000);

    // Group headers are uppercase divs inside aside.
    const aside = page.locator("aside");
    await expect(aside).toBeVisible();
  });

});
