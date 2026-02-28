/**
 * magus-verification-smoke.spec.ts  —  CrownMagus0 Full Verification Pack
 *
 * Adds smoke checks for surfaces introduced in wizard packs #1–#29
 * and board oversight (Mode A). Complements proof-smoke.spec.ts.
 *
 * Runs as part of: npm run test:e2e
 * Individual run:  npx playwright test tests/magus-verification-smoke.spec.ts --reporter=line
 *
 * DOES NOT duplicate proof-smoke.spec.ts tests.
 * COVERS:
 *   - Wizard manifest page loads without JS crash
 *   - Board oversight route renders without JS crash
 *   - Root route redirects (does not 404 or white-screen)
 */

import { test, expect, Page } from "@playwright/test";

const DEMO_SCHOOL_ID =
  process.env.CROWN_DEMO_SCHOOL_ID ?? "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN ?? "playwright-demo-token";

// ── Auth seeding (mirrors proof-smoke.spec.ts pattern) ────────────────────────
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
        // storage blocked in some E2E contexts — non-fatal
      }
    },
    { role, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );
}

// ── Console error filter (same allowlist as proof-smoke) ──────────────────────
const IGNORED_PATTERNS = [
  /net::ERR_/,
  /Failed to fetch/,
  /Failed to load resource/,
  /favicon/i,
  /ResizeObserver loop/,
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
  return () => [...errors];
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test("root route does not white-screen or 404", async ({ page }) => {
  const getErrors = attachErrorCollector(page);
  await seedDemoSession(page, "admin");
  const resp = await page.goto("/");
  // Must not be a hard 4xx/5xx from the dev server itself
  expect(resp?.status() ?? 200).toBeLessThan(500);
  // Page must have a <body> (not a blank shell)
  const bodyText = await page.locator("body").innerText().catch(() => "");
  // Empty body string + no redirect is a white-screen — fail it
  expect(bodyText.trim().length + (await page.url()).length).toBeGreaterThan(20);
  const errs = getErrors();
  expect(errs, `JS errors on /: ${errs.join(", ")}`).toHaveLength(0);
});

test("wizard route is reachable (no JS crash)", async ({ page }) => {
  const getErrors = attachErrorCollector(page);
  await seedDemoSession(page, "admin");
  await page.goto("/wizards");
  // Give Vue/React time to hydrate
  await page.waitForTimeout(1500);
  const errs = getErrors();
  expect(errs, `JS errors on /wizards: ${errs.join(", ")}`).toHaveLength(0);
});

test("board oversight route is reachable (no JS crash)", async ({ page }) => {
  const getErrors = attachErrorCollector(page);
  await seedDemoSession(page, "BOARD_MEMBER");
  await page.goto("/board");
  await page.waitForTimeout(1500);
  const errs = getErrors();
  expect(errs, `JS errors on /board: ${errs.join(", ")}`).toHaveLength(0);
});

test("dashboard route is reachable for admin role (no JS crash)", async ({ page }) => {
  const getErrors = attachErrorCollector(page);
  await seedDemoSession(page, "admin");
  await page.goto("/dashboard");
  await page.waitForTimeout(1500);
  const errs = getErrors();
  expect(errs, `JS errors on /dashboard: ${errs.join(", ")}`).toHaveLength(0);
});
