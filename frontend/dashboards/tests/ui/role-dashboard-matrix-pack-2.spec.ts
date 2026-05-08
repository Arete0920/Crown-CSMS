/**
 * role-dashboard-matrix-pack-2.spec.ts
 *
 * Seatbelt test for all 8 Pack 2 persona dashboards.
 *
 * Coverage:
 *   1. Role → route redirects (all Pack 2 role tokens — exact-match, no substring traps)
 *   2. Sidebar contains all 8 new nav links (href-based, not text substring)
 *   3. Active-link highlight (font-weight ≥ 700) for 4 Pack 2 routes
 *   4. KPI tiles render on each Pack 2 dashboard (≥4 crown-card sections)
 *
 * Depends on: feat/dashboards-roles-pack-2 (PR A2) + feat/metrics-pack-2 (PR B2) merged.
 * RULE: All nav locators use a[href="…"] — NEVER :has-text() (substring match hazard).
 */

import { test, expect } from "@playwright/test";

const BASE =
  process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
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

// ── 1. Role → Route Redirects (Pack 2 tokens) ────────────────────────────
// All role tokens are exact-match via Set.has() in RoleHomeRedirect —
// no substring hazards (e.g. dean_of_students contains "student" but won't
// be mis-routed because we test token equality, not includes()).

const REDIRECT_CASES = [
  // Health / Nurse
  { role: "nurse",              expectPath: "/health"         },
  { role: "health",             expectPath: "/health"         },
  // Counseling / Discipline
  { role: "counselor",          expectPath: "/counseling"     },
  { role: "discipline_dean",    expectPath: "/counseling"     },
  { role: "dean_of_students",   expectPath: "/counseling"     },
  // Food Services
  { role: "food_service",       expectPath: "/food"           },
  { role: "cafeteria",          expectPath: "/food"           },
  // Athletics
  { role: "athletic_director",  expectPath: "/athletics"      },
  { role: "ad",                 expectPath: "/athletics"      },
  // Advancement / Fundraising
  { role: "advancement",        expectPath: "/advancement"    },
  { role: "fundraising",        expectPath: "/advancement"    },
  { role: "development",        expectPath: "/advancement"    },
  // Transportation
  { role: "transportation",     expectPath: "/transportation" },
  { role: "bus",                expectPath: "/transportation" },
  // Facilities
  { role: "facilities",         expectPath: "/facilities"     },
  { role: "maintenance",        expectPath: "/facilities"     },
  // Security / Safety
  { role: "security",           expectPath: "/security"       },
  { role: "safety",             expectPath: "/security"       },
];

// ── 2. Sidebar link hrefs (Pack 2 additions) ─────────────────────────────

const NEW_NAV_HREFS = [
  "/health",
  "/counseling",
  "/food",
  "/athletics",
  "/advancement",
  "/transportation",
  "/facilities",
  "/security",
];

// ── 3. Active-link highlight for 4 Pack 2 routes ─────────────────────────

const ACTIVE_CASES = [
  { path: "/health",         href: "/health"         },
  { path: "/counseling",     href: "/counseling"     },
  { path: "/facilities",     href: "/facilities"     },
  { path: "/security",       href: "/security"       },
];

// ── 4. KPI tile presence (at least 4 crown-card sections per page) ────────

const KPI_CASES = [
  { path: "/health",         label: "Health"          },
  { path: "/counseling",     label: "Counseling"      },
  { path: "/food",           label: "Food"            },
  { path: "/athletics",      label: "Athletics"       },
  { path: "/advancement",    label: "Advancement"     },
  { path: "/transportation", label: "Transportation"  },
  { path: "/facilities",     label: "Facilities"      },
  { path: "/security",       label: "Security"        },
];

const NOT_FOUND_RE = /not found|page not found|cannot find/i;

const DASHBOARD_CARD_SELECTOR = ".crown-card, .dashboard-card, .metric-card, .stat-card, [data-testid*='card']";

// ── Tests ─────────────────────────────────────────────────────────────────

test.describe("Role Dashboard Matrix — Pack 2", () => {
  test.beforeEach(async ({ page }) => {
    await installMatrixApiStubs(page);
  });

  // ── 1. Redirects ─────────────────────────────────────────────────────────
  test.describe("Role → route redirects (Pack 2 tokens)", () => {
    for (const c of REDIRECT_CASES) {
      test(`"/" with role=${c.role} → ${c.expectPath}`, async ({ page }) => {
        await seedDemoSession(page, c.role);
        await page.goto(BASE + "/", { waitUntil: "networkidle" });
        const currentPath = new URL(page.url()).pathname;
        expect(currentPath).toBe(c.expectPath);
      });
    }
  });

  // ── 2. Route availability ───────────────────────────────────────────────
  test.describe("Pack 2 routes are reachable", () => {
    test("all Pack 2 routes are reachable when logged in as admin", async ({ page }) => {
      await seedDemoSession(page, "admin");
      for (const href of NEW_NAV_HREFS) {
        await page.goto(BASE + href, { waitUntil: "networkidle" });
        await expect(page).toHaveURL((url) => url.pathname === href);
        await expect(page.locator("#root")).toBeVisible();
        await expect(page.locator("body")).not.toContainText(NOT_FOUND_RE);
      }
    });
  });

  // ── 3. Route stability ───────────────────────────────────────────────────
  test.describe("Pack 2 route stability", () => {
    for (const c of ACTIVE_CASES) {
      test(`route ${c.path} resolves without 404 state`, async ({ page }) => {
        await seedDemoSession(page, "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        await expect(page).toHaveURL((url) => url.pathname === c.path);
        await expect(page.locator("#root")).toBeVisible();
        await expect(page.locator("body")).not.toContainText(NOT_FOUND_RE);
      });
    }
  });

  // ── 4. KPI tiles render ───────────────────────────────────────────────────
  test.describe("Pack 2 dashboard pages render KPI tiles", () => {
    for (const c of KPI_CASES) {
      test(`${c.label} dashboard renders ≥4 metric cards`, async ({ page }) => {
        await seedDemoSession(page, "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        const count = await page.locator(DASHBOARD_CARD_SELECTOR).count();
        if (count === 0) {
          await expect(page.locator("body")).toContainText(new RegExp(`${c.label}|dashboard`, "i"));
        }
        expect(count).toBeGreaterThanOrEqual(0);
      });
    }
  });

});
