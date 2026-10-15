import { test, expect } from "@playwright/test";

// This is a UI denial proof; it is NOT proof that the backend separately
// authorizes real API calls or that any token in sessionStorage is genuine.
const deniedPaths = [
  "/board", "/hr", "/settings", "/wizards", "/aftercare/roster",
  "/students/synthetic-nonexistent", "/board-executive",
];

test.describe("anonymous CROWN school route denial", () => {
  for (const path of deniedPaths) {
    test(`anonymous visitor cannot render protected ${path}`, async ({ page }) => {
      const protectedCalls: string[] = [];
      page.on("request", (request) => {
        if (/\/api\/v1\/(?:nav|wizards)\//.test(request.url())) {
          protectedCalls.push(request.url());
        }
      });
      await page.goto(path, { waitUntil: "domcontentloaded" });
      await expect(page).toHaveURL(/\/not-authorized$/);
      await expect(page.getByText("Access Restricted", { exact: true })).toBeVisible();
      expect(protectedCalls).toHaveLength(0);
    });
  }

  test("anonymous login remains accessible", async ({ page }) => {
    await page.goto("/login", { waitUntil: "domcontentloaded" });
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.locator("form").first()).toBeVisible();
  });
});
