import { test, expect, Page } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = process.env.DEMO_BASE_URL || "http://localhost:3000";
const DEMO_EMAIL = process.env.DEMO_EMAIL || "playwright@crown-demo.local";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD || "PlaywrightDemo1!";

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
  await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });

  const email = page.locator('input[type="email"], input[name="email"]').first();
  const password = page.locator('input[type="password"], input[name="password"]').first();
  const submit = page.getByRole("button", { name: /sign in|log in|login|continue/i }).first();

  await expect(email).toBeVisible({ timeout: 15000 });
  await expect(password).toBeVisible({ timeout: 15000 });

  await email.fill(DEMO_EMAIL);
  await password.fill(DEMO_PASSWORD);
  await submit.click();

  await expect(page).toHaveURL(/\/admin(?:[/?#]|$)/, { timeout: 15000 });
  await assertPageHealthy(page, "post-login-admin");
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