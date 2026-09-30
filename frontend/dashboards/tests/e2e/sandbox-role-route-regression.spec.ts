import { test, expect } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:3000";
const IS_SANDBOX =
  process.env.CERT_SANDBOX_MODE === "1" ||
  process.env.VITE_SANDBOX_MODE === "1" ||
  process.env.VITE_DEMO_MODE === "sandbox";

const creds = {
  admin: {
    roleValue: "school_admin",
    email: process.env.CERT_SANDBOX_ADMIN_EMAIL || "admin@heritage.example.org",
    password: process.env.CERT_SANDBOX_ADMIN_PASSWORD || "",
    expected: IS_SANDBOX ? /school-admin-dashboard|admin|director|wizards/i : /admin|director|wizards/i,
    forbidden: [/\/director\/aid\b/],
  },
  parent: {
    roleValue: "parent",
    email: process.env.CERT_PARENT_EMAIL || "parent.reed@heritage.example.org",
    password: process.env.CERT_PARENT_PASSWORD || "",
    expected: /parent|portal|dashboard|home/i,
    forbidden: [/\/admin\b/, /\/director\/aid\b/, /\/finance\b/, /school-admin-dashboard/],
  },
  teacher: {
    roleValue: "teacher",
    email: process.env.CERT_TEACHER_EMAIL || "teacher.lower@heritage.example.org",
    password: process.env.CERT_TEACHER_PASSWORD || "",
    expected: /teacher|dashboard|home/i,
    forbidden: [/\/admin\b/, /\/director\/aid\b/, /\/finance\b/, /school-admin-dashboard/],
  },
  student: {
    roleValue: "student",
    email: process.env.CERT_STUDENT_EMAIL || "student.avery.reed11@heritage.example.org",
    password: process.env.CERT_STUDENT_PASSWORD || "",
    expected: /student|dashboard|home/i,
    forbidden: [
      /\/admin\b/,
      /\/director\/aid\b/,
      /\/finance\b/,
      /school-admin-dashboard/,
      /\/admissions(?:-dashboard|\/pipeline)?\b/,
      /\/teacher\b/,
    ],
  },
};

async function login(page, email, password, roleValue) {
  if (!IS_SANDBOX && !password) {
    throw new Error(`Credential is required for role ${roleValue}`);
  }
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });

  const path = new URL(page.url()).pathname;
  if (path !== "/" && path !== "/login") {
    return "already-authenticated";
  }

  const roleSelect = page.locator("#login-role").first();
  if (IS_SANDBOX && (await roleSelect.count()) > 0) {
    await expect(roleSelect).toBeVisible();
    await roleSelect.selectOption(roleValue);

    const previewButton = page.getByRole("button", { name: /continue to heritage preview/i }).first();
    await expect(previewButton).toBeVisible();
    await previewButton.click();
    await expect(page, `sandbox ${roleValue} preview must establish a real backend session`).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
    return "sandbox-preview";
  }

  const emailInput = page.locator('input[type="email"], input[name*="email"], input[placeholder*="@"]').first();
  const passwordInput = page.locator('input[type="password"]').first();

  if ((await emailInput.count()) > 0 && (await passwordInput.count()) > 0) {
    if ((await roleSelect.count()) > 0 && roleValue) {
      const option = roleSelect.locator(`option[value="${roleValue}"]`);
      if ((await option.count()) > 0) {
        await roleSelect.selectOption(roleValue);
      }
    }

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    if (await emailInput.isEditable()) {
      await emailInput.fill(email);
    }
    if (await passwordInput.isEditable()) {
      await passwordInput.fill(password);
    }
    await page.getByRole("button", { name: /sign in|login/i }).first().click();
    await page.waitForLoadState("networkidle");

    await expect(page, `${roleValue} credentials must establish a real authenticated session`).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
    return "credentials";
  }

  throw new Error(`No supported real authentication path was available for role ${roleValue}`);
}

for (const [roleName, role] of Object.entries(creds)) {
  test(`sandbox role route regression :: ${roleName}`, async ({ page }) => {
    await login(page, role.email, role.password, role.roleValue);
    await page.waitForLoadState("networkidle");

    await expect(page).toHaveURL(role.expected, { timeout: 30000 });
    await page.reload({ waitUntil: "networkidle" });
    await expect(page).toHaveURL(role.expected, { timeout: 30000 });

    const probeRoutes = [
      "/admin",
      "/director/aid/",
      "/finance",
      "/school-admin-dashboard",
      "/admissions-dashboard",
      "/admissions/pipeline",
      "/teacher",
      "/sandbox",
    ];

    for (const route of probeRoutes) {
      await page.goto(`${frontendUrl}${route}`, { waitUntil: "networkidle" });
      for (const forbidden of role.forbidden) {
        await expect(page).not.toHaveURL(forbidden);
      }
    }
  });
}
