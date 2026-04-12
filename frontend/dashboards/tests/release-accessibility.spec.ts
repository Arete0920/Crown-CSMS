import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const routes = ["/login", "/admin", "/teacher", "/parent", "/student"];

for (const route of routes) {
  test(`a11y smoke ${route}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const serious = results.violations.filter(v => v.impact === "serious" || v.impact === "critical");
    expect(serious, `Serious/critical violations on ${route}`).toEqual([]);
  });
}