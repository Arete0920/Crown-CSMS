import { test, expect } from "@playwright/test";

const BASE = process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
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
        // ignore — storage may be unavailable in some contexts
      }
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}

// ── 1. Role → Route Redirect ────────────────────────────────────────────────
//    Every role that maps to a persona dashboard must land there when hitting /.

const REDIRECT_CASES = [
  { role: IS_SANDBOX ? "school_admin" : "admin", expectPath: IS_SANDBOX ? "/school-admin-dashboard" : "/admin" },
  { role: "director",   expectPath: IS_SANDBOX ? "/not-authorized" : "/admin" },
  { role: "principal",  expectPath: IS_SANDBOX ? "/not-authorized" : "/admin" },
  { role: "board",      expectPath: "/board"   },
  { role: "governor",   expectPath: "/board"   },
  { role: "finance",    expectPath: "/finance" },
  { role: "biz_office", expectPath: "/finance" },
];

// ── 2. Sidebar nav labels ───────────────────────────────────────────────────
//    All 8 links that CrownLayout.jsx renders must appear in the aside.

const NAV_LABELS = [
  "Administration",
  "School Board",
  "Finance",
  "Financial Aid",
  "Admissions",
  "Academics",
  "Billing",
  "System Integrity",
];

// ── 3. Active-link highlight ────────────────────────────────────────────────
//    The link whose href matches the current path must be bold (font-weight 700).
//    We land on each route as an admin so the sidebar is always rendered.

const ACTIVE_CASES = [
  { path: IS_SANDBOX ? "/school-admin-dashboard" : "/admin", label: "Administration" },
  { path: "/board",   label: "School Board"   },
  { path: "/finance", label: "Finance"        },
];

// ── Tests ───────────────────────────────────────────────────────────────────

test.describe("Nav + Role Routing", () => {
  // ── 1. Redirects ──────────────────────────────────────────────────────────
  test.describe("Role → route redirect", () => {
    for (const c of REDIRECT_CASES) {
      test(`"/" redirects for role=${c.role} → ${c.expectPath}`, async ({ page }) => {
        await seedDemoSession(page, c.role);
        await page.goto(BASE + "/", { waitUntil: "networkidle" });
        await page.waitForTimeout(250);
        await expect(page).toHaveURL(
          new RegExp(`${c.expectPath.replace("/", "\\/")}$`)
        );
      });
    }
  });

  // ── 2. Sidebar labels ─────────────────────────────────────────────────────
  test.describe("Sidebar nav labels", () => {
    test("all 8 nav links are visible on /admin", async ({ page }) => {
      await seedDemoSession(page, IS_SANDBOX ? "school_admin" : "admin");
      await page.goto(BASE + (IS_SANDBOX ? "/school-admin-dashboard" : "/admin"), { waitUntil: "networkidle" });

      if (IS_SANDBOX) {
        await expect(page.locator("body")).toContainText(/School Administrator Dashboard|School Snapshot/i);
        return;
      }

      for (const label of NAV_LABELS) {
        await expect(
          page.locator(`aside a:has-text("${label}")`)
        ).toBeVisible();
      }
    });
  });

  // ── 3. Active link bold ───────────────────────────────────────────────────
  test.describe("Active nav highlight", () => {
    for (const c of ACTIVE_CASES) {
      test(`"${c.label}" link is bold when on ${c.path}`, async ({ page }) => {
        await seedDemoSession(page, IS_SANDBOX ? "school_admin" : "admin");
        await page.goto(BASE + c.path, { waitUntil: "networkidle" });

        if (IS_SANDBOX && c.path === "/school-admin-dashboard") {
          await expect(page.locator("body")).toContainText(/School Administrator Dashboard|School Snapshot/i);
          return;
        }

        const link = page.locator(`aside a:has-text("${c.label}")`).first();
        await expect(link).toBeVisible();

        const fontWeight = await link.evaluate(
          (el) => window.getComputedStyle(el).fontWeight
        );
        // CrownLayout sets font-weight:700 on the matching route
        expect(Number(fontWeight)).toBeGreaterThanOrEqual(700);
      });
    }
  });
});
