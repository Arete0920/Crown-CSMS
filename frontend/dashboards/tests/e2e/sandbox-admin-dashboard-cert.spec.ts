import { test, expect } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:3000";
const primaryEmail = process.env.CERT_SANDBOX_ADMIN_EMAIL || "admin@heritage.test";
const primaryPassword = process.env.CERT_SANDBOX_ADMIN_PASSWORD || "Crown2026!";
const secondEmail = process.env.CERT_SANDBOX_SECOND_ADMIN_EMAIL || "admin@harvest.test";
const secondPassword = process.env.CERT_SANDBOX_SECOND_ADMIN_PASSWORD || "Crown2026!";
const schoolAdminRoute = process.env.CERT_SCHOOL_ADMIN_ROUTE || "/school-admin-dashboard";

async function login(page, email, password) {
  await page.goto(frontendUrl, { waitUntil: "networkidle" });
  const emailInput = page.locator('input[type="email"], input[name*="email"], input[placeholder*="@"]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  // Support both sandbox login surfaces:
  // 1) credential form, 2) role-card button flow.
  if ((await emailInput.count()) > 0 && (await passwordInput.count()) > 0) {
    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();

    if (await emailInput.isEditable()) {
      await emailInput.fill(email);
    }
    if (await passwordInput.isEditable()) {
      await passwordInput.fill(password);
    }

    const signInButton = page.getByRole("button", { name: /sign in|login/i }).first();
    await signInButton.click();
    return "credentials";
  }

  const sandboxRoleButton = page.getByRole("button", { name: /school sandbox/i }).first();
  if ((await sandboxRoleButton.count()) > 0) {
    await expect(sandboxRoleButton).toBeVisible();
    await sandboxRoleButton.click();
    return "role-card";
  }

  const demoLoginButton = page.getByRole("button", { name: /demo login/i }).first();
  await expect(demoLoginButton).toBeVisible();
  await demoLoginButton.click();
  return "devjwt";
}

test("sandbox admin lands on redesigned dashboard and stays out of legacy routes", async ({ page }) => {
  const loginMode = await login(page, primaryEmail, primaryPassword);
  if (loginMode === "devjwt") {
    await page.waitForLoadState("networkidle");
    await expect(page).not.toHaveURL(/director\/aid/);
  } else {
    await page.waitForURL(new RegExp(`${schoolAdminRoute.replace("/", "\\/")}`), { timeout: 30000 });
    await expect(page).toHaveURL(new RegExp(`${schoolAdminRoute.replace("/", "\\/")}`));

    await page.reload({ waitUntil: "networkidle" });
    await expect(page).toHaveURL(new RegExp(`${schoolAdminRoute.replace("/", "\\/")}`));

    await page.goto(`${frontendUrl}/admin`, { waitUntil: "networkidle" });
    await expect(page).toHaveURL(new RegExp(`${schoolAdminRoute.replace("/", "\\/")}`));
  }

  await page.goto(`${frontendUrl}/director/aid/`, { waitUntil: "networkidle" });
  await expect(page).not.toHaveURL(/director\/aid/);
});

test("second sandbox admin also lands on redesigned dashboard", async ({ page }) => {
  const loginMode = await login(page, secondEmail, secondPassword);
  if (loginMode === "devjwt") {
    await page.waitForLoadState("networkidle");
    await expect(page).not.toHaveURL(/director\/aid/);
    return;
  }

  await page.waitForURL(new RegExp(`${schoolAdminRoute.replace("/", "\\/")}`), { timeout: 30000 });
  await expect(page).toHaveURL(new RegExp(`${schoolAdminRoute.replace("/", "\\/")}`));
});
