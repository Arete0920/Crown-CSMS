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
      for (const v of serious) {
        const targets = v.nodes.flatMap((n) => n.target || []).join(", ");
        console.warn(`[a11y][serious] ${route} :: ${v.id} :: ${targets}`);
        for (const n of v.nodes) {
          if (n.failureSummary) {
            console.warn(`[a11y][serious-detail] ${route} :: ${v.id} :: ${(n.target || []).join(' | ')} :: ${n.failureSummary.replace(/\s+/g, ' ').trim()}`);
          }
        }
      }
    }

    expect(critical, `Critical accessibility violations on ${route}`).toEqual([]);
  });
}
