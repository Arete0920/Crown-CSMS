/**
 * proof-smoke.spec.ts  —  Crown2026 UI Proof Gate
 *
 * This is the CI gate. It must stay fast (<90 s total) and deterministic.
 * It proves five critical paths load and render in demo-session mode.
 *
 * DOES NOT:
 *   - validate real API auth (uses seeded demo session)
 *   - test business logic (that is covered by backend proof tests)
 *
 * HARD FAILS on:
 *   - JS console errors (page.on "error" + console "error")
 *   - Missing page-identity heading
 *   - Route redirect failures
 */

import { test, expect, Page } from "@playwright/test";

const BASE =
  process.env.CROWN_UI_URL ??
  process.env.VITE_DEV_BASE_URL ??
  "http://localhost:4173";

const DEMO_SCHOOL_ID =
  process.env.CROWN_DEMO_SCHOOL_ID ?? "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN =
  process.env.CROWN_DEMO_TOKEN ?? "playwright-demo-token";

// ── Auth seeding ──────────────────────────────────────────────────────────────
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
        // storage blocked in some contexts — non-fatal
      }
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}

// ── Console error collection ──────────────────────────────────────────────────
// Filters out benign browser noise so only real JS errors fail the gate.
const IGNORED_PATTERNS = [
  /net::ERR_/,             // network failures hitting stub API in CI
  /Failed to fetch/,       // same
  /Failed to load resource/,  // API 4xx/5xx from backend in dev/CI (UI-only test)
  /favicon/i,              // favicon 404 common in CI
  /ResizeObserver loop/,   // browser implementation noise
];

function attachErrorCollector(page: Page): () => string[] {
  const errors: string[] = [];
  page.on("pageerror", (err) => errors.push(`[pageerror] ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() !== "error") return;
    const text = msg.text();
    if (IGNORED_PATTERNS.some((re) => re.test(text))) return;
    errors.push(`[console.error] ${text}`);
  });
  return () => errors;
}

// ── Critical paths ────────────────────────────────────────────────────────────

test.describe("Crown2026 UI Proof Gate", () => {
  const isSandbox = process.env.VITE_DEMO_MODE === "sandbox" || process.env.VITE_SANDBOX_MODE === "1";
  const adminSeedRole = isSandbox ? "school_admin" : "admin";
  const expectedAdminHome =
    isSandbox
      ? /\/school-admin-dashboard$/
      : /\/admin$/;

  // ── 1. Role home redirect ───────────────────────────────────────────────────
  test("/ redirects admin role → /admin", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await seedDemoSession(page, adminSeedRole);
    await page.goto(BASE + "/", { waitUntil: "networkidle" });
    await page.waitForTimeout(300);

    await expect(page).toHaveURL(expectedAdminHome);
    expect(getErrors()).toHaveLength(0);
  });

  test("/ redirects teacher role → /teacher", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await seedDemoSession(page, "teacher");
    await page.goto(BASE + "/", { waitUntil: "networkidle" });
    await page.waitForTimeout(300);

    await expect(page).toHaveURL(/\/teacher$/);
    expect(getErrors()).toHaveLength(0);
  });

  test("/ redirects parent role → /parent", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await seedDemoSession(page, "parent");
    await page.goto(BASE + "/", { waitUntil: "networkidle" });
    await page.waitForTimeout(300);

    await expect(page).toHaveURL(/\/parent$/);
    expect(getErrors()).toHaveLength(0);
  });

  // ── 2. Admin dashboard ──────────────────────────────────────────────────────
  test("/admin renders heading and quick-action links", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await seedDemoSession(page, adminSeedRole);
    await page.goto(BASE + (isSandbox ? "/school-admin-dashboard" : "/admin"), { waitUntil: "networkidle" });

    // Dashboard identity should be visible even if semantics use h4/h6 hierarchy.
    await expect(page.locator("h1, h2, h3, h4, h5, h6").first()).toBeVisible();
    await expect(page.locator("body")).toContainText(/School Administrator Dashboard|School Snapshot|Executive Dashboard/i);

    expect(getErrors()).toHaveLength(0);
  });

  // ── 3. Teacher attendance ───────────────────────────────────────────────────
  test("/teacher/attendance renders without JS errors", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await seedDemoSession(page, "teacher");
    await page.goto(BASE + "/teacher/attendance", { waitUntil: "networkidle" });

    // Page heading or form control must be present
    const heading = page.locator("h1, h2, h3").first();
    await expect(heading).toBeVisible();

    expect(getErrors()).toHaveLength(0);
  });

  // ── 4. Parent dashboard ─────────────────────────────────────────────────────
  test("/parent renders heading without JS errors", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await seedDemoSession(page, "parent");
    await page.goto(BASE + "/parent", { waitUntil: "networkidle" });

    await expect(page.locator("h1, h2").first()).toBeVisible();

    expect(getErrors()).toHaveLength(0);
  });

  // ── 5. Gradebook RO ──────────────────────────────────────────────────────
  test("/gradebook renders heading without JS errors", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await seedDemoSession(page, adminSeedRole);
    await page.goto(BASE + "/gradebook", { waitUntil: "networkidle" });

    await expect(page.locator("h1, h2").first()).toBeVisible();

    expect(getErrors()).toHaveLength(0);
  });

  // ── 6. Login page is publicly accessible (no session) ──────────────────────
  test("/login renders without session", async ({ page }) => {
    const getErrors = attachErrorCollector(page);
    await page.goto(BASE + "/login", { waitUntil: "networkidle" });

    await expect(page.locator("h1, h2, form").first()).toBeVisible();

    expect(getErrors()).toHaveLength(0);
  });
});
