import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

async function openAdminSandbox(page: Page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("school_admin");
  await page.getByRole("button", { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

async function verifySchoolAdminCannotEnterPlatformAuthority(page: Page) {
  const forbidden = [
    { path: "/master-control-dashboard", pattern: /\/master-control-dashboard(?:$|\?)/i },
    { path: "/release-reliability-dashboard", pattern: /\/release-reliability-dashboard(?:$|\?)/i },
  ];
  for (const target of forbidden) {
    await page.goto(`${frontendUrl}${target.path}`, { waitUntil: "networkidle" });
    await expect(page, `School Administrator must be denied platform authority at ${target.path}`).not.toHaveURL(target.pattern);
  }
}

test("sandbox school administrator reviews context, resolves exception, and communicates", async ({ page }) => {
  await openAdminSandbox(page);
  await page.goto(`${frontendUrl}/school-admin-dashboard`, { waitUntil: "domcontentloaded" });
  const panel = page.getByTestId("sandbox-admin-transaction");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText("HCA-0001");
  await expect(page.getByTestId("admin-enrollment-context")).toContainText("ENROLLED");
  await expect(page.getByTestId("admin-academic-context")).toContainText("B+");
  await expect(page.getByTestId("admin-tuition-context")).not.toHaveText("$0.00");
  await expect(page.getByTestId("admin-finance-summary")).toContainText("open");
  await expect(page.getByTestId("admin-platform-authority")).toHaveText("School-scoped administrator");
  const actionPromise = page.waitForResponse((response) => response.url().includes("/api/v1/sandbox/admin/resolve-operational-exception/") && response.request().method() === "POST", { timeout: 30000 });
  await panel.getByRole("button", { name: "Verify + Resolve + Send Follow-up" }).click();
  const response = await actionPromise;
  expect(response.ok(), `admin transaction returned ${response.status()}`).toBeTruthy();
  const payload = await response.json();
  expect(payload.student_household_update_persisted).toBe(true);
  expect(payload.attendance_exception_resolved).toBe(true);
  expect(payload.communication_sent).toBe(true);
  expect(payload.is_platform_superuser).toBe(false);
  await expect(page.getByTestId("admin-attendance-status")).toHaveText("EXCUSED");
  await expect(page.getByTestId("admin-exception-status")).toHaveText("resolved");
  await expect(page.getByTestId("admin-household-note")).toHaveText("Admin-verified demo household");
  await expect(page.getByTestId("admin-communication-status")).toHaveText("sent");
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("admin-exception-status")).toHaveText("resolved");
  await expect(page.getByTestId("admin-household-note")).toHaveText("Admin-verified demo household");
  await expect(page.getByTestId("admin-communication-status")).toHaveText("sent");
  await expect(page.getByTestId("admin-platform-authority")).toHaveText("School-scoped administrator");
  await verifySchoolAdminCannotEnterPlatformAuthority(page);
});
