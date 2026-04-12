import { test, expect } from "@playwright/test";

const baseRoutes = [
  "/",
  "/login",
  "/admin",
  "/teacher",
  "/parent",
  "/student",
];

for (const route of baseRoutes) {
  test(`route smoke ${route}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();
  });
}