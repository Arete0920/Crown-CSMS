import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:4173";

// Use the Heritage demo school UUID (safe default used throughout your demo wiring).
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";

// Non-empty token is enough for UI route guards + RoleHomeRedirect.
// This test is UI-proof only; it intentionally does not validate API auth.
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";

const ROUTES = [
  { name: "/parent", path: "/parent", role: "parent" },
  { name: "/student", path: "/student", role: "student" },
];

async function seedDemoSession(page, role: string) {
  await page.addInitScript(({ role, token, schoolId }) => {
    try {
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.role", role);
      sessionStorage.setItem("crown.school.id", schoolId);

      // Some older paths may read localStorage; mirror there defensively.
      localStorage.setItem("crown.jwt.access", token);
      localStorage.setItem("crown.role", role);
      localStorage.setItem("crown.school.id", schoolId);
      localStorage.setItem("crown.demo.role", role);
    } catch {
      // ignore
    }
  }, { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID });
}

async function assertDashboard(page, path: string) {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });

  await page.goto(BASE + path, { waitUntil: "networkidle" });
  await page.waitForTimeout(250);

  await expect(page.locator("[data-testid='dashboard-grid'], main").first()).toBeVisible();

  // Must render at least one content surface inside the dashboard shell.
  const contentBlocks = await page
    .locator(
      ".crown-card, [data-testid='dashboard-grid'] article, [data-testid='dashboard-grid'] section, [data-testid='dashboard-grid'] [role='listitem'], ul, table"
    )
    .count();
  expect(contentBlocks, "Expected dashboard content blocks").toBeGreaterThanOrEqual(1);
  expect(errors, "No console errors expected").toHaveLength(0);
}

test.describe("Dashboard proof (role homes)", () => {
  for (const r of ROUTES) {
    test(r.name + " renders cleanly", async ({ page }) => {
      await seedDemoSession(page, r.role);
      await assertDashboard(page, r.path);
    });
  }
});
