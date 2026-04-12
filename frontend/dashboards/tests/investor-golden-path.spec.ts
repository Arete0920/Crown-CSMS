import { test, expect } from "@playwright/test";

test("golden path: admissions to billing to attendance", async ({ page }) => {
  await page.goto("/login");

  // Replace with your deterministic demo login flow.
  // Suggested env vars:
  // PLAYWRIGHT_USER
  // PLAYWRIGHT_PASS

  await page.waitForLoadState("networkidle");

  // Admissions
  await expect(page.locator("body")).toContainText(/admissions|dashboard|student/i);

  // Enrollment
  // Replace selectors below with real stable test ids once present.
  const body = page.locator("body");
  await expect(body).toContainText(/enrollment|student|family/i);

  // Billing
  await expect(body).toContainText(/billing|tuition|payment|finance/i);

  // Attendance
  await expect(body).toContainText(/attendance/i);

  // Parent / student / admin consistency
  await expect(body).toContainText(/student|family|account|status/i);
});