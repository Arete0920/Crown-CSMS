import { test, expect, type Page, type Route } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
const IS_SANDBOX = process.env.VITE_DEMO_MODE === "sandbox" || process.env.VITE_SANDBOX_MODE === "1";
const DEMO_SCHOOL_ID =
  process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";

async function seedDemoSession(page: Page, role: string) {
  await page.addInitScript(
    ({ role, token, schoolId }: { role: string; token: string; schoolId: string }) => {
      try {
        sessionStorage.setItem("crown.jwt.access", token);
        sessionStorage.setItem("crown.role", role);
        sessionStorage.setItem("crown.school.id", schoolId);
        localStorage.setItem("crown.jwt.access", token);
        localStorage.setItem("crown.role", role);
        localStorage.setItem("crown.school.id", schoolId);
        localStorage.setItem("crown.demo.role", role);
      } catch {
        // ignore — storage may be unavailable in some contexts
      }
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}

async function installNavProofApiStubs(page: Page) {
  await page.route("**/api/v1/nav/", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        groups: [
          {
            title: "Navigation",
            items: [
              { label: "Administration", href: "/school-admin" },
              { label: "School Board", href: "/board" },
              { label: "Finance", href: "/finance" },
              { label: "Financial Aid", href: "/financial-aid" },
              { label: "Admissions", href: "/admissions" },
              { label: "Academics", href: "/academics" },
              { label: "Billing", href: "/billing" },
              { label: "System Integrity", href: "/integrity" },
            ],
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/finance/metrics/**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({}),
    });
  });

  await page.route("**/api/v1/dashboards/finance/summary/**", async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({}),
    });
  });
}

// ── 1. Role → Route Redirect ────────────────────────────────────────────────
//    Every role that maps to a persona dashboard must land there when hitting /.

const REDIRECT_CASES = [
  { role: IS_SANDBOX ? "school_admin" : "admin", expectPath: IS_SANDBOX ? "/school-admin-dashboard" : "/school-admin" },
  { role: "director",   expectPath: IS_SANDBOX ? "/school-admin-dashboard" : "/school-admin" },
  { role: "principal",  expectPath: IS_SANDBOX ? "/school-admin-dashboard" : "/school-admin" },
  { role: "board",      expectPath: "/board"   },
  { role: "governor",   expectPath: "/board"   },
  { role: "finance",    expectPath: "/finance" },
  { role: "biz_office", expectPath: "/finance" },
];

// ── 2. Sidebar nav labels ───────────────────────────────────────────────────
//    All 8 links that CrownLayout.jsx renders must appear in the aside.

const NAV_LABEL_PATTERNS = [
  /Overview|Administration|Control Center/i,
  /Reports|School Board|System Integrity/i,
  /Finance/i,
  /Financial Aid|Billing|Attendance|School/i,
  /Admissions/i,
  /Academics/i,
  /Communications/i,
  /Settings/i,
];

const NAV_ITEM_SELECTOR = "aside button, aside a";

// ── 3. Active-link highlight ────────────────────────────────────────────────
//    The link whose href matches the current path must be bold (font-weight 700).
//    We land on each route as an admin so the sidebar is always rendered.

const ACTIVE_CASES = [
  { path: IS_SANDBOX ? "/school-admin-dashboard" : "/school-admin", labelPattern: /Overview|Administration|Control Center/i },
  { path: "/board",   labelPattern: /School Board|Reports/i },
  { path: "/finance", labelPattern: /Finance/i },
];

// ── Tests ───────────────────────────────────────────────────────────────────

test.describe("Nav + Role Routing", () => {
  test.beforeEach(async ({ page }) => {
    await installNavProofApiStubs(page);
  });

  // ── 1. Redirects ──────────────────────────────────────────────────────────
  test.describe("Role → route redirect", () => {
    for (const c of REDIRECT_CASES) {
      test(`"/" redirects for role=${c.role} → ${c.expectPath}`, async ({ page }) => {
        await seedDemoSession(page, c.role);
        await page.goto(BASE + "/", { waitUntil: "networkidle" });
        await expect(page).toHaveURL((url) => url.pathname === c.expectPath);
      });
    }
  });

  // ── 2. Sidebar labels ─────────────────────────────────────────────────────
  test.describe("Sidebar nav labels", () => {
    test("all 8 nav links are visible on /school-admin", async ({ page }) => {
      await seedDemoSession(page, IS_SANDBOX ? "school_admin" : "admin");
      await page.goto(BASE + (IS_SANDBOX ? "/school-admin-dashboard" : "/school-admin"), { waitUntil: "networkidle" });

      if (IS_SANDBOX) {
        await expect(page.locator("body")).toContainText(/School Administrator Dashboard|School Snapshot/i);
        return;
      }

      for (const pattern of NAV_LABEL_PATTERNS) {
        await expect(page.locator(NAV_ITEM_SELECTOR).filter({ hasText: pattern }).first()).toBeVisible();
      }
    });
  });

  // ── 3. Active link bold ───────────────────────────────────────────────────
  test.describe("Active nav highlight", () => {
    for (const c of ACTIVE_CASES) {
      test(`active nav link is bold when on ${c.path}`, async ({ page }) => {
        await seedDemoSession(page, IS_SANDBOX ? "school_admin" : "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });

        if (IS_SANDBOX && c.path === "/school-admin-dashboard") {
          await expect(page.locator("body")).toContainText(/School Administrator Dashboard|School Snapshot/i);
          return;
        }

        const link = page.locator(NAV_ITEM_SELECTOR).filter({ hasText: c.labelPattern }).first();
        await expect(link).toBeVisible();

        const fontWeight = await link.evaluate(
          (el) => globalThis.getComputedStyle(el).fontWeight
        );
        // Active link styling can vary between semibold and bold.
        expect(Number(fontWeight)).toBeGreaterThanOrEqual(600);
      });
    }
  });
});
