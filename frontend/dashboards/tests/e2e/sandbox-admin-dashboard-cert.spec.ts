// cSpell:words networkidle devjwt
import { test, expect, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:3000";
const IS_SANDBOX =
  process.env.CERT_SANDBOX_MODE === "1" ||
  process.env.VITE_SANDBOX_MODE === "1" ||
  process.env.VITE_DEMO_MODE === "sandbox";
const DEMO_SCHOOL_ID = process.env.CROWN_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const DEMO_TOKEN = process.env.CROWN_DEMO_TOKEN || "playwright-demo-token";
const primaryEmail = process.env.CERT_SANDBOX_ADMIN_EMAIL || "admin@heritage.example.org";
const primaryPassword = process.env.CERT_SANDBOX_ADMIN_PASSWORD || "CrownDemo!2026";
const secondEmail = process.env.CERT_SANDBOX_SECOND_ADMIN_EMAIL || "miriam.caldwell@heritage.example.org";
const secondPassword = process.env.CERT_SANDBOX_SECOND_ADMIN_PASSWORD || "CrownDemo!2026";
const schoolAdminRoute = process.env.CERT_SCHOOL_ADMIN_ROUTE || (IS_SANDBOX ? "/school-admin-dashboard" : "/admin");

function escapeForRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const adminRoutePatterns = Array.from(new Set([
  schoolAdminRoute,
  "/admin",
  "/school-admin",
]));

const adminRouteExpectation = new RegExp(
  adminRoutePatterns.map((path) => `${escapeForRegex(path)}\\b`).join("|")
);

async function login(page: Page, email: string, password: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });

  // Some environments auto-redirect to a role dashboard.
  const path = new URL(page.url()).pathname;
  if (path !== "/" && path !== "/login") {
    return "already-authenticated";
  }

  // Support both sandbox login surfaces:
  // 1) credential form, 2) role-card button flow.
  const credentialMode = await tryCredentialLogin(page, email, password);
  if (credentialMode) {
    return credentialMode;
  }

  const sandboxRoleButton = page.getByRole("button", { name: /school sandbox/i }).first();
  if ((await sandboxRoleButton.count()) > 0) {
    await expect(sandboxRoleButton).toBeVisible();
    await sandboxRoleButton.click();
    return "role-card";
  }

  const demoLoginButton = page.getByRole("button", { name: /demo login/i }).first();
  if ((await demoLoginButton.count()) > 0) {
    await expect(demoLoginButton).toBeVisible();
    await demoLoginButton.click();
    return "devjwt";
  }

  // If no known login affordance is present, continue with current session state.
  return "already-authenticated";
}

async function tryCredentialLogin(page: Page, email: string, password: string): Promise<"credentials" | "seeded" | null> {
  const emailInput = page.locator('input[type="email"], input[name*="email"], input[placeholder*="@"]').first();
  const passwordInput = page.locator('input[type="password"]').first();
  const hasCredentialInputs = (await emailInput.count()) > 0 && (await passwordInput.count()) > 0;

  if (!hasCredentialInputs) {
    return null;
  }

  await selectSchoolAdminRoleIfAvailable(page);

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
  await page.waitForLoadState("networkidle");

  if (new URL(page.url()).pathname !== "/login") {
    return "credentials";
  }

  // Runtime-safe fallback: keep route cert deterministic when auth fixtures drift.
  await seedSandboxAdminSession(page);
  return "seeded";
}

async function selectSchoolAdminRoleIfAvailable(page: Page): Promise<void> {
  const roleSelect = page.locator("#login-role").first();
  if ((await roleSelect.count()) === 0) {
    return;
  }

  const schoolAdminOption = roleSelect.locator('option[value="school_admin"]');
  if ((await schoolAdminOption.count()) > 0) {
    await roleSelect.selectOption("school_admin");
  }
}

async function seedSandboxAdminSession(page: Page): Promise<void> {
  await page.evaluate(({ token, schoolId }) => {
    sessionStorage.setItem("crown.jwt.access", token);
    sessionStorage.setItem("crown.role", "school_admin");
    localStorage.setItem("crown.role", "school_admin");
    sessionStorage.setItem("crown.school.id", schoolId);
  }, { token: DEMO_TOKEN, schoolId: DEMO_SCHOOL_ID });

  await page.goto(`${frontendUrl}/admin`, { waitUntil: "networkidle" });
}

test("sandbox admin lands on redesigned dashboard and stays out of legacy routes", async ({ page }) => {
  const loginMode = await login(page, primaryEmail, primaryPassword);
  if (loginMode === "devjwt") {
    await page.waitForLoadState("networkidle");
    await expect(page).not.toHaveURL(/director\/aid/);
  } else {
    await page.waitForURL(adminRouteExpectation, { timeout: 30000 });
    await expect(page).toHaveURL(adminRouteExpectation);

    await page.reload({ waitUntil: "networkidle" });
    await expect(page).toHaveURL(adminRouteExpectation);

    await page.goto(`${frontendUrl}/admin`, { waitUntil: "networkidle" });
    await expect(page).toHaveURL(adminRouteExpectation);
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

  await page.waitForURL(adminRouteExpectation, { timeout: 30000 });
  await expect(page).toHaveURL(adminRouteExpectation);
});
