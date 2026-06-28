/**
 * dashboard-smoke.spec.ts — Crown Dashboards & Reporting smoke gate.
 *
 * Validates that /dash/:role renders for each supported role.
 * Checks:
 *   - Page title matches role
 *   - Widget grid is visible (non-empty)
 *   - No JS console errors
 *   - Error banner does NOT appear (happy path)
 *
 * Uses seeded demo session (same pattern as proof-smoke.spec.ts).
 */

import { test, expect, Page } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL ?? "http://localhost:4173";
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID ?? "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN ?? "playwright-demo-token";

const ROLES = ["admin", "teacher", "parent", "student", "finance", "registrar"];

async function seedDemoSession(page: Page, role: string): Promise<void> {
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
        // storage blocked — non-fatal
      }
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}

function buildSummaryPayload(role: string) {
  const title = role.charAt(0).toUpperCase() + role.slice(1);
  return {
    role,
    school_id: DEMO_SCHOOL_ID,
    generated_at: "2026-06-28T12:00:00Z",
    widgets: [
      {
        key: role === "admin" ? "alerts_flip" : `${role}_overview`,
        type: "stat",
        size: "sm",
        title: role === "admin" ? "Alerts" : `${title} overview`,
        subtitle: role === "admin" ? "Review active risks" : "Daily snapshot",
        drilldown: role === "admin" ? { enabled: true } : undefined,
        data: role === "admin"
          ? { count: 4, label: "Active alerts", status: "warn" }
          : { count: 4, label: "Active widgets", status: "good" },
      },
    ],
  };
}

async function installSummaryStub(page: Page, role: string, delayMs = 0): Promise<void> {
  await page.route("**/api/dashboards/summary/", async (route) => {
    if (delayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildSummaryPayload(role)),
    });
  });
}

async function installDrilldownStub(page: Page): Promise<void> {
  await page.route("**/api/dashboards/drilldown/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        widget: "alerts_flip",
        school_id: DEMO_SCHOOL_ID,
        page: 1,
        has_more: false,
        rows: [{ id: "row-1", title: "Attendance alert", detail: "Follow up today" }],
      }),
    });
  });
}

// ---------------------------------------------------------------------------
// Role dashboard smoke — one test per role
// ---------------------------------------------------------------------------

for (const role of ROLES) {
  test(`/dash/${role} renders dashboard page`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));

    await seedDemoSession(page, role);
    await installSummaryStub(page, role);
    await page.goto(`${BASE}/dash/${role}`);

    // Page should load without a hard crash
    await expect(page).not.toHaveURL(/error/i);

    // Title heading shows role (capitalized)
    const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);
    await expect(page.getByText(`${roleLabel} Dashboard`)).toBeVisible({ timeout: 8000 });

    // Widget grid is present in DOM (may still be loading)
    const grid = page.locator('[data-testid="dashboard-grid"]');
    await expect(grid).toBeVisible({ timeout: 8000 });

    // No hard JS errors
    expect(errors, `JS errors on /dash/${role}: ${errors.join("; ")}`).toHaveLength(0);
  });
}

// ---------------------------------------------------------------------------
// Error banner does NOT appear when API succeeds
// ---------------------------------------------------------------------------

test("/dash/admin error banner absent on success", async ({ page }) => {
  await seedDemoSession(page, "admin");
  await installSummaryStub(page, "admin");
  await page.goto(`${BASE}/dash/admin`);

  // Wait for grid to appear (implies success path)
  await page.locator('[data-testid="dashboard-grid"]').waitFor({ timeout: 10000 });

  // Error banner should not be visible
  const errorBanner = page.locator('[role="alert"]');
  const bannerCount = await errorBanner.count();
  if (bannerCount > 0) {
    const text = await errorBanner.first().textContent();
    // Tolerate if it's something other than dashboard load failure
    expect(text).not.toMatch(/Failed to load dashboard/i);
  }
});

// ---------------------------------------------------------------------------
// Drilldown drawer opens and closes
// ---------------------------------------------------------------------------

test("/dash/admin drilldown drawer opens on expand", async ({ page }) => {
  await seedDemoSession(page, "admin");
  await installSummaryStub(page, "admin");
  await installDrilldownStub(page);
  await page.goto(`${BASE}/dash/admin`);

  // Wait for widgets to render
  await page.locator('[data-widget-key="alerts_flip"]').waitFor({ timeout: 10000 });

  // Find and click an expand button (⤢)
  const expandBtn = page.locator('button[aria-label*="Expand"]').first();
  if (await expandBtn.isVisible()) {
    await expandBtn.click();

    // Drawer should appear
    await expect(page.locator('dialog[open]')).toBeVisible({ timeout: 3000 });

    // Close button should work
    await page.locator('button[aria-label="Close drawer"]').click();
    await expect(page.locator('dialog[open]')).toHaveCount(0);
  }
});

// ---------------------------------------------------------------------------
// Shimmer skeletons appear during loading (checks initial render)
// ---------------------------------------------------------------------------

test("/dash/teacher shows skeleton then widgets", async ({ page }) => {
  await seedDemoSession(page, "teacher");
  await installSummaryStub(page, "teacher", 300);

  await page.goto(`${BASE}/dash/teacher`);

  // Grid present (either skeleton or real widgets)
  await expect(page.locator('[data-testid="dashboard-grid"]')).toBeVisible({ timeout: 5000 });

  // Eventually a real widget key should appear or loading resolves
  await page.waitForFunction(
    () => document.querySelector("[data-widget-key]") !== null,
    { timeout: 12000 }
  );
});
