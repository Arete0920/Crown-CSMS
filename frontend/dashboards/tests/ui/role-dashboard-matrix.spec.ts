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

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:3000";
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
  // Marketing / Advancement
  { role: "marketing",     expectPath: "/marketing"     },
  { role: "advancement",   expectPath: "/marketing"     },
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

// ── 3. Active-link bold (new routes) ─────────────────────────────────────

const ACTIVE_CASES = [
  { path: "/it",            label: "IT"            },
  { path: "/marketing",     label: "Marketing"     },
  { path: "/spiritual-life",label: "Spiritual Life" },
  { path: "/office",        label: "Office / HR"   },
];

// ── Tests ────────────────────────────────────────────────────────────────

test.describe("Role Dashboard Matrix", () => {
  // ── 1. Redirects ────────────────────────────────────────────────────────
  test.describe("Role → route redirects (new dashboards)", () => {
    for (const c of REDIRECT_CASES) {
      test(`"/" redirects for role=${c.role} → ${c.expectPath}`, async ({ page }) => {
        await seedDemoSession(page, c.role);
        await page.goto(BASE + "/", { waitUntil: "networkidle" });
        await page.waitForTimeout(250);
        await expect(page).toHaveURL(
          new RegExp(`${c.expectPath.replace(/\//g, "\\/")}$`)
        );
      });
    }
  });

  // ── 2. Sidebar labels ───────────────────────────────────────────────────
  test.describe("Sidebar nav contains new labels", () => {
    test("all new nav links visible on /admin (admin session)", async ({ page }) => {
      await seedDemoSession(page, "admin");
      await page.goto(BASE + "/admin", { waitUntil: "networkidle" });
      for (const { href } of NEW_NAV_LABELS) {
        await expect(
          page.locator(`aside a[href="${href}"]`)
        ).toBeVisible();
      }
    });
  });

  // ── 3. Active highlight ─────────────────────────────────────────────────
  test.describe("Active nav link is bold on new routes", () => {
    for (const c of ACTIVE_CASES) {
      test(`"${c.label}" link is bold when on ${c.path}`, async ({ page }) => {
        await seedDemoSession(page, "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });
        const link = page.locator(`aside a[href="${c.path}"]`).first();
        await expect(link).toBeVisible();
        const fontWeight = await link.evaluate(
          (el) => window.getComputedStyle(el).fontWeight
        );
        expect(Number(fontWeight)).toBeGreaterThanOrEqual(700);
      });
    }
  });
});
