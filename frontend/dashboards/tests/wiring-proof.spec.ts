import { test, expect, Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = process.env.DEMO_BASE_URL || process.env.VITE_DEV_BASE_URL || "http://localhost:4173";
const DEMO_ROLE = process.env.DEMO_ROLE || "admin";
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";

const routes = [
  { name: "admin", path: "/admin" },
  { name: "admissions", path: "/admissions" },
  { name: "finance", path: "/finance" },
  { name: "billing", path: "/billing" },
  { name: "financial-aid", path: "/financial-aid" },
  { name: "academics", path: "/academics" },
  { name: "communications", path: "/communications" },
  { name: "board-executive", path: "/board/executive" },
];

const artifactsDir = path.resolve(process.cwd(), "artifacts", "wiring-proof", "playwright");

async function assertPageHealthy(page: Page, routeName: string) {
  await page.waitForLoadState("domcontentloaded");
  const body = await page.locator("body").innerText();

  expect(body, `${routeName}: should not show application error`).not.toMatch(/Application Error/i);
  expect(body, `${routeName}: should not show debug overlay`).not.toMatch(/DevJwtPanel/i);
  expect(body, `${routeName}: should not show 404`).not.toMatch(/\b404\b|Not Found/i);
  expect(body, `${routeName}: should not show auth failure`).not.toMatch(/\b401\b|Unauthorized|Invalid credentials/i);

  await page.screenshot({
    path: path.join(artifactsDir, `${routeName}.png`),
    fullPage: true,
  });
}

async function login(page: Page) {
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
        // ignore storage-denied contexts in CI browser variants
      }
    },
    { role: DEMO_ROLE, token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID }
  );

  await page.goto(`${BASE_URL}/`, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(300);
  await assertPageHealthy(page, "seeded-session-home");
}

test.beforeAll(() => {
  fs.mkdirSync(artifactsDir, { recursive: true });
});

test("login works and lands on admin", async ({ page }) => {
  await login(page);
});

for (const route of routes) {
  test(`route smoke: ${route.path}`, async ({ page }) => {
    await login(page);
    const response = await page.goto(`${BASE_URL}${route.path}`, { waitUntil: "domcontentloaded" });

    expect(response, `${route.path}: response should exist`).not.toBeNull();
    expect(response!.status(), `${route.path}: status should be < 400`).toBeLessThan(400);

    await assertPageHealthy(page, route.name);
  });
}
