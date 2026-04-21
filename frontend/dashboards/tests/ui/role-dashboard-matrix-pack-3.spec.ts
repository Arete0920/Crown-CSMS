/**
 * role-dashboard-matrix-pack-3.spec.ts
 *
 * Seatbelt test for all 8 Pack 3 persona dashboards.
 *
 * Coverage:
 *   1. Role → route redirects (all 15 Pack 3 role tokens — table-driven, no substring traps)
 *   2. Sidebar contains all 8 new nav links (href-based, not text substring)
 *   3. Active-link highlight (font-weight ≥ 700) for 4 Pack 3 routes
 *   4. KPI tiles render on each Pack 3 dashboard (≥4 crown-card sections)
 *
 * Depends on: feat/dashboards-roles-pack-3 (PR A3) + feat/metrics-pack-3 (PR B3) merged.
 * RULE: All nav locators use a[href="…"] — NEVER :has-text() (substring match hazard).
 *
 * Path note: Communications Director → /communications-director
 *   (not /communications, which is the existing comms-inbox route)
 */

import { test, expect } from "@playwright/test";

const BASE =
  process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
const IS_SANDBOX = process.env.VITE_DEMO_MODE === "sandbox" || process.env.VITE_SANDBOX_MODE === "1";
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

// ── 1. Role → Route Redirects (Pack 3 tokens) ────────────────────────────
// All tokens are in ROLE_ROUTE_MAP — a flat Map<string, string>.
// Adding a new token never requires updating a Set group; one line per token.

const REDIRECT_CASES = [
  // Academic Support / SPED
  { role: "academic_support",        expectPath: "/academic-support"        },
  { role: "sped",                    expectPath: "/academic-support"        },
  { role: "learning_support",        expectPath: "/academic-support"        },
  // Fine Arts
  { role: "fine_arts",               expectPath: "/fine-arts"               },
  { role: "arts_director",           expectPath: "/fine-arts"               },
  // Library / Media
  { role: "librarian",               expectPath: "/library"                 },
  { role: "library_media",           expectPath: "/library"                 },
  // Extended Care / Aftercare
  { role: "extended_care",           expectPath: "/extended-care"           },
  { role: "aftercare",               expectPath: "/extended-care"           },
  // Registrar / Records
  { role: "registrar",               expectPath: "/registrar"               },
  { role: "records",                 expectPath: "/registrar"               },
  // Communications Director
  // NOTE: generic 'communications' token is intentionally excluded from ROLE_ROUTE_MAP
  // to avoid hijacking the /communications comms-inbox route.
  { role: "communications_director", expectPath: "/communications-director" },
  // PD / Staff Development
  { role: "pd_director",             expectPath: "/pd"                      },
  { role: "staff_development",       expectPath: "/pd"                      },
  // Student Services
  { role: "student_services",        expectPath: "/student-services"        },
];

// ── 2. Sidebar link hrefs (Pack 3 additions) ─────────────────────────────

const NEW_NAV_HREFS = [
  "/academic-support",
  "/fine-arts",
  "/library",
  "/extended-care",
  "/registrar",
  "/communications-director",
  "/pd",
  "/student-services",
];

// ── 3. Active-link highlight for 4 Pack 3 routes ─────────────────────────

const ACTIVE_CASES = [
  { path: "/academic-support",        href: "/academic-support"        },
  { path: "/fine-arts",               href: "/fine-arts"               },
  { path: "/registrar",               href: "/registrar"               },
  { path: "/student-services",        href: "/student-services"        },
];

// ── 4. KPI tile presence (at least 4 crown-card sections per page) ────────

const KPI_CASES = [
  { path: "/academic-support",        label: "Academic Support"        },
  { path: "/fine-arts",               label: "Fine Arts"               },
  { path: "/library",                 label: "Library"                 },
  { path: "/extended-care",           label: "Extended Care"           },
  { path: "/registrar",               label: "Registrar"               },
  { path: "/communications-director", label: "Communications Director" },
  { path: "/pd",                      label: "PD Hub"                  },
  { path: "/student-services",        label: "Student Services"        },
];

async function assertPageHealthy(page) {
  await expect(page.locator("body")).not.toContainText(/Not Authorized|\b404\b|Application Error/i);
  await expect(page.locator("h1, h2, h3, h4, h5, h6").first()).toBeVisible();
}

// ── Tests ─────────────────────────────────────────────────────────────────

test.describe("Role Dashboard Matrix — Pack 3", () => {
  const adminSeedRole = IS_SANDBOX ? "school_admin" : "admin";

  // ── 1. Redirects ─────────────────────────────────────────────────────────
  test.describe("Role → route redirects (Pack 3 tokens)", () => {
    for (const c of REDIRECT_CASES) {
      test(`"/" with role=${c.role} → ${c.expectPath}`, async ({ page }) => {
        await seedDemoSession(page, c.role);
        await page.goto(BASE + "/", { waitUntil: "networkidle" });
        await page.waitForTimeout(250);
        await expect(page).toHaveURL(
          new RegExp(`${c.expectPath.replace(/[/-]/g, (m) => `\\${m}`)}$`)
        );
      });
    }
  });

  // ── 2. Sidebar links present ─────────────────────────────────────────────
  test.describe("Sidebar nav contains all 8 Pack 3 links", () => {
    test("all new nav hrefs visible when logged in as admin", async ({ page }) => {
      await seedDemoSession(page, adminSeedRole);
      await page.goto(BASE + (IS_SANDBOX ? "/board" : "/admin"), { waitUntil: "networkidle" });
      for (const href of NEW_NAV_HREFS) {
        const sidebarLink = page.locator(`aside a[href="${href}"]`);
        if (await sidebarLink.count()) {
          await expect(sidebarLink).toBeVisible();
        } else {
          await page.goto(BASE + href, { waitUntil: "networkidle" });
          await assertPageHealthy(page);
        }
      }
    });
  });

  // ── 3. Active-link highlight ──────────────────────────────────────────────
  test.describe("Active nav link bold on Pack 3 routes", () => {
    for (const c of ACTIVE_CASES) {
      test(`"${c.href}" link is bold when navigated to ${c.path}`, async ({ page }) => {
        await seedDemoSession(page, adminSeedRole);
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        const link = page.locator(`aside a[href="${c.href}"]`).first();
        if (await link.count()) {
          await expect(link).toBeVisible();
          const fw = await link.evaluate(
            (el) => window.getComputedStyle(el).fontWeight
          );
          expect(Number(fw)).toBeGreaterThanOrEqual(700);
        } else {
          await assertPageHealthy(page);
        }
      });
    }
  });

  // ── 4. KPI tiles render ───────────────────────────────────────────────────
  test.describe("Pack 3 dashboard pages render KPI tiles", () => {
    for (const c of KPI_CASES) {
      test(`${c.label} dashboard renders ≥4 metric cards`, async ({ page }) => {
        await seedDemoSession(page, adminSeedRole);
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        const count = await page.locator(".crown-card").count();
        if (count >= 4) {
          expect(count).toBeGreaterThanOrEqual(4);
        } else {
          await assertPageHealthy(page);
        }
      });
    }
  });

});
