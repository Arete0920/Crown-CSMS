import { expect, test } from "@playwright/test";

// Presentation-only typography check: no sign-in or tenant mutation.
for (const [width, height] of [[1440, 900], [390, 844]]) {
  test(`login form controls inherit CROWN typography at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height });
    await page.goto("/login");

    const root = page.locator(".login-root");
    await expect(root).toBeVisible();
    const font = await root.evaluate((element) => getComputedStyle(element).fontFamily);
    expect(font).toContain("Inter");

    for (const selector of ["#login-role", ".btn-signin"]) {
      const control = page.locator(selector);
      await expect(control).toBeVisible();
      expect(await control.evaluate((element) => getComputedStyle(element).fontFamily)).toBe(font);
    }
    const fields = page.locator(".field-input");
    for (let index = 0; index < await fields.count(); index++) {
      expect(await fields.nth(index).evaluate((element) => getComputedStyle(element).fontFamily)).toBe(font);
    }
  });
}
