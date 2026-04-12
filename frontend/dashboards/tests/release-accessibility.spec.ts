import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const routes = ["/login", "/admin", "/teacher", "/parent", "/student"];

for (const route of routes) {
  test(`a11y smoke ${route}`, async ({ page }) => {
    await page.goto(route);
    await page.waitForLoadState("networkidle");
    await expect(page.locator("body")).toBeVisible();

    const results = await new AxeBuilder({ page }).analyze();
    const critical = results.violations.filter(v => v.impact === "critical");
    const serious = results.violations.filter(v => v.impact === "serious");

    if (serious.length > 0) {
      // Keep serious violations visible in CI logs while gating release on critical failures.
      console.warn(`[a11y][serious] ${route}: ${serious.length} serious violations`);
    }

    expect(critical, `Critical accessibility violations on ${route}`).toEqual([]);
  });
}