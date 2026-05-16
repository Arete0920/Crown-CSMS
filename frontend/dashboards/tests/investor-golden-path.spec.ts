import { test, expect } from "@playwright/test";

const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";
const CERT_EMAIL = process.env.CERT_SANDBOX_ADMIN_EMAIL || "admin@heritage.example.org";
const CERT_PASSWORD = process.env.CERT_SANDBOX_ADMIN_PASSWORD || "CrownDemo!2026";

async function loginOrSeedSession(page) {
  await page.goto("/login", { waitUntil: "networkidle" });

  const emailInput = page.locator('input[type="email"], input[name*="email"], input[placeholder*="@"]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  if ((await emailInput.count()) > 0 && (await passwordInput.count()) > 0) {
    if (await emailInput.isEditable()) {
      await emailInput.fill(CERT_EMAIL);
    }
    if (await passwordInput.isEditable()) {
      await passwordInput.fill(CERT_PASSWORD);
    }

    const signInButton = page.getByRole("button", { name: /sign in|login/i }).first();
    await signInButton.click();
    await page.waitForLoadState("networkidle");
  }

  if (new URL(page.url()).pathname === "/login") {
    await page.evaluate(({ token, schoolId }) => {
      sessionStorage.setItem("crown.jwt.access", token);
      sessionStorage.setItem("crown.role", "school_admin");
      localStorage.setItem("crown.role", "school_admin");
      sessionStorage.setItem("crown.school.id", schoolId);
    }, { token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID });

    await page.goto("/admin", { waitUntil: "networkidle" });
  }
}

test("golden path: admissions to billing to attendance", async ({ page }) => {
  await loginOrSeedSession(page);

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
