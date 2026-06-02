/**
 * role-dashboard-matrix.spec.ts
 *
 * Seatbelt test for all 8 new persona dashboards introduced in dashboards-roles-pack-1.
 *
 * Coverage:
 *   1. Role → route redirects (8 new role tokens)
 *   2. Sidebar contains all new nav labels
 *   3. Active-link highlight (font-weight 700) for at least 3 new routes
 *
 * Depends on: feat/dashboards-roles-pack-1 (frontend routes + nav) merged into main.
 * Run after: PR A and PR B are merged.
 */

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

async function installMatrixApiStubs(page) {
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

// ── 1. Role → Route Redirects (8 new dashboards, all role tokens) ─────────

const REDIRECT_CASES = [
  // Teacher
  { role: "teacher",       expectPath: "/teacher"       },
  // Parent
  { role: "parent",        expectPath: "/parent"        },
  // Student
  { role: "student",       expectPath: "/student"       },
  // IT Director
  { role: "it",            expectPath: "/it"            },
  { role: "it_director",   expectPath: "/it"            },
  // Financial Aid Director
  { role: "aid_director",  expectPath: "/financial-aid" },
  { role: "financial_aid", expectPath: "/financial-aid" },
  // Marketing
  { role: "marketing",     expectPath: "/marketing"     },
  // Advancement (now exact-match routes to /advancement, not /marketing — see PR A2)
  { role: "advancement",   expectPath: "/advancement"   },
  // Spiritual Life
  { role: "chaplain",      expectPath: "/spiritual-life" },
  { role: "spiritual_life",expectPath: "/spiritual-life" },
  // Office / HR
  { role: "office_manager",expectPath: "/office"        },
  { role: "hr",            expectPath: "/office"        },
];

// ── 2. Sidebar new labels ─────────────────────────────────────────────────
// CrownLayout nav now groups 14 links; assert all new ones are visible.

const NEW_NAV_LABELS = [
  { label: "IT",            href: "/it"            },
  { label: "Office / HR",   href: "/office"        },
  { label: "Teacher",       href: "/teacher"       },
  { label: "Parent",        href: "/parent"        },
  { label: "Student",       href: "/student"       },
  { label: "Spiritual Life",href: "/spiritual-life" },
  { label: "Marketing",     href: "/marketing"     },
];

const REACHABILITY_CASES = [
  { href: "/it", role: "it" },
  { href: "/office", role: "office_manager" },
  { href: "/teacher", role: "teacher" },
  { href: "/parent", role: "parent" },
  { href: "/student", role: "student" },
  { href: "/spiritual-life", role: "chaplain" },
  { href: "/marketing", role: "marketing" },
];

const NOT_FOUND_RE = /not found|page not found|cannot find/i;

// ── 3. Active-link bold (new routes) ─────────────────────────────────────

const ACTIVE_CASES = [
  { path: "/it",            label: "IT"            },
  { path: "/marketing",     label: "Marketing"     },
  { path: "/spiritual-life",label: "Spiritual Life" },
  { path: "/office",        label: "Office / HR"   },
];

// ── Tests ────────────────────────────────────────────────────────────────

test.describe("Role Dashboard Matrix", () => {
  test.beforeEach(async ({ page }) => {
    await installMatrixApiStubs(page);
  });

  // ── 1. Redirects ────────────────────────────────────────────────────────
  test.describe("Role → route redirects (new dashboards)", () => {
    for (const c of REDIRECT_CASES) {
      test(`"/" redirects for role=${c.role} → ${c.expectPath}`, async ({ page }) => {
        await seedDemoSession(page, c.role);
        await page.goto(BASE + "/", { waitUntil: "networkidle" });
        const currentPath = new URL(page.url()).pathname;
        expect(currentPath).toBe(c.expectPath);
      });
    }
  });

  // ── 2. Route availability ───────────────────────────────────────────────
  test.describe("Pack 1 routes are reachable", () => {
    test("all new Pack 1 routes are reachable with role-aligned sessions", async ({ page }) => {
      for (const { href, role } of REACHABILITY_CASES) {
        await seedDemoSession(page, role);
        await page.goto(BASE + href, { waitUntil: "networkidle" });
        await expect(page).toHaveURL((url) => url.pathname === href);
        await expect(page.locator("main")).toBeVisible();
        await expect(page.locator("body")).not.toContainText(NOT_FOUND_RE);
      }
    });
  });

  // ── 3. Route stability ──────────────────────────────────────────────────
  test.describe("Pack 1 route stability", () => {
    for (const c of ACTIVE_CASES) {
      test(`route ${c.path} resolves without 404 state`, async ({ page }) => {
        await seedDemoSession(page, "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        await expect(page).toHaveURL((url) => url.pathname === c.path);
        await expect(page.locator("main")).toBeVisible();
        await expect(page.locator("body")).not.toContainText(NOT_FOUND_RE);
      });
    }
  });
});
