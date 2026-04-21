import { test, expect } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:3000";

const creds = {
  admin: {
    email: process.env.CERT_SANDBOX_ADMIN_EMAIL || "admin@heritage.test",
    password: process.env.CERT_SANDBOX_ADMIN_PASSWORD || "Crown2026!",
    expected: /school-admin-dashboard|admin/i,
    forbidden: [/\/director\/aid\b/, /\/finance\b/],
  },
  parent: {
    email: process.env.CERT_PARENT_EMAIL || "parent@heritage.test",
    password: process.env.CERT_PARENT_PASSWORD || "Crown2026!",
    expected: /parent|portal|dashboard|home/i,
    forbidden: [/\/admin\b/, /\/director\/aid\b/, /\/finance\b/, /school-admin-dashboard/],
  },
  teacher: {
    email: process.env.CERT_TEACHER_EMAIL || "teacher@heritage.test",
    password: process.env.CERT_TEACHER_PASSWORD || "Crown2026!",
    expected: /teacher|dashboard|home/i,
    forbidden: [/\/admin\b/, /\/director\/aid\b/, /\/finance\b/, /school-admin-dashboard/],
  },
  finance: {
    email: process.env.CERT_FINANCE_EMAIL || "finance@heritage.test",
    password: process.env.CERT_FINANCE_PASSWORD || "Crown2026!",
    expected: /finance|billing|aid|dashboard|home/i,
    forbidden: [/school-admin-dashboard/],
  },
  admissions: {
    email: process.env.CERT_ADMISSIONS_EMAIL || "admissions@heritage.test",
    password: process.env.CERT_ADMISSIONS_PASSWORD || "Crown2026!",
    expected: /admissions|applications|dashboard|home/i,
    forbidden: [/school-admin-dashboard/],
  },
};

async function login(page, email, password) {
  await page.goto(frontendUrl, { waitUntil: "networkidle" });
  const emailInput = page.locator('input[type="email"], input[name*="email"], input[placeholder*="@"]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  if ((await emailInput.count()) > 0 && (await passwordInput.count()) > 0) {
    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    if (await emailInput.isEditable()) {
      await emailInput.fill(email);
    }
    if (await passwordInput.isEditable()) {
      await passwordInput.fill(password);
    }
    await page.getByRole("button", { name: /sign in|login/i }).first().click();
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

for (const [roleName, role] of Object.entries(creds)) {
  test(`sandbox role route regression :: ${roleName}`, async ({ page }) => {
    const loginMode = await login(page, role.email, role.password);
    await page.waitForLoadState("networkidle");

    if (loginMode !== "devjwt") {
      await expect(page).toHaveURL(role.expected, { timeout: 30000 });
      await page.reload({ waitUntil: "networkidle" });
      await expect(page).toHaveURL(role.expected, { timeout: 30000 });
    }

    const probeRoutes = loginMode === "devjwt"
      ? ["/director/aid/", "/finance", "/school-admin-dashboard"]
      : [
          "/admin",
          "/director/aid/",
          "/finance",
          "/school-admin-dashboard",
          "/sandbox",
        ];

    for (const route of probeRoutes) {
      await page.goto(`${frontendUrl}${route}`, { waitUntil: "networkidle" });
      for (const forbidden of role.forbidden) {
        if (loginMode === "devjwt" && String(forbidden) === String(/\/admin\b/)) {
          continue;
        }
        await expect(page).not.toHaveURL(forbidden);
      }
    }
  });
}
