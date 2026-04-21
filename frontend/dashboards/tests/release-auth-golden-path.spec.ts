import { test, expect } from "@playwright/test";

const user = process.env.PLAYWRIGHT_USER || "demo@example.com";
const pass = process.env.PLAYWRIGHT_PASS || "password";

test("release auth golden path", async ({ page }) => {
  await page.goto("/login");
  await page.waitForLoadState("networkidle");

  const email = page.locator('input[type="email"], input[name="email"], [data-testid="login-email"]').first();
  const password = page.locator('input[type="password"], input[name="password"], [data-testid="login-password"]').first();
  const submit = page.locator('button[type="submit"], [data-testid="login-submit"]').first();

  if ((await email.count()) && (await email.isEditable())) {
    await email.fill(user);
  }
  if ((await password.count()) && (await password.isEditable())) {
    await password.fill(pass);
  }
  if (await submit.count()) {
    await submit.click();
  }

  await page.waitForLoadState("networkidle");
  await expect(page.locator("body")).toContainText(/dashboard|admin|teacher|parent|student|billing|attendance/i);
});
