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
  process.env.VITE_DEV_BASE_URL || "http://localhost:3000";
const DEMO_SCHOOL_ID =
  process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "";

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

// ── Tests ─────────────────────────────────────────────────────────────────

test.describe("Role Dashboard Matrix — Pack 2", () => {
  test.skip(!DEMO_TOKEN, "CROWN_DEMO_TOKEN is required for dashboard role tests");

  // ── 1. Redirects ─────────────────────────────────────────────────────────
  test.describe("Role → route redirects (Pack 2 tokens)", () => {
    for (const c of REDIRECT_CASES) {
      test(`"/" with role=${c.role} → ${c.expectPath}`, async ({ page }) => {
        await seedDemoSession(page, c.role);
        await page.goto(BASE + "/", { waitUntil: "networkidle" });
        await page.waitForTimeout(250);
        await expect(page).toHaveURL(
          new RegExp(`${c.expectPath.replace(/\//g, "\\/")}$`)
        );
      });
    }
  });

  // ── 2. Sidebar links present ─────────────────────────────────────────────
  test.describe("Sidebar nav contains all 8 Pack 2 links", () => {
    test("all new nav links visible when logged in as admin", async ({ page }) => {
      await seedDemoSession(page, "admin");
      await page.goto(BASE + "/admin", { waitUntil: "networkidle" });
      for (const href of NEW_NAV_HREFS) {
        // href-based locator — not text substring — safe for all labels
        await expect(
          page.locator(`aside a[href="${href}"]`)
        ).toBeVisible();
      }
    });
  });

  // ── 3. Active-link highlight ──────────────────────────────────────────────
  test.describe("Active nav link bold on Pack 2 routes", () => {
    for (const c of ACTIVE_CASES) {
      test(`"${c.href}" link is bold when navigated to ${c.path}`, async ({ page }) => {
        await seedDemoSession(page, "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        const link = page.locator(`aside a[href="${c.href}"]`).first();
        await expect(link).toBeVisible();
        const fw = await link.evaluate(
          (el) => window.getComputedStyle(el).fontWeight
        );
        expect(Number(fw)).toBeGreaterThanOrEqual(700);
      });
    }
  });

  // ── 4. KPI tiles render ───────────────────────────────────────────────────
  test.describe("Pack 2 dashboard pages render KPI tiles", () => {
    for (const c of KPI_CASES) {
      test(`${c.label} dashboard renders ≥4 metric cards`, async ({ page }) => {
        await seedDemoSession(page, "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        // Each CrownMetricCard → CrownCard → <section class="crown-card">
        const count = await page.locator(".crown-card").count();
        expect(count).toBeGreaterThanOrEqual(4);
      });
    }
  });

});
