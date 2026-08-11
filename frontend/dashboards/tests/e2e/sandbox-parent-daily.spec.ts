import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

async function openParentSandbox(page: Page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("parent");
  await page.getByRole("button", { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test("sandbox parent reviews child attendance progress communications billing and staff denials", async ({ page }) => {
  await openParentSandbox(page);
  await page.goto(`${frontendUrl}/parent`, { waitUntil: "networkidle" });

  const panel = page.getByTestId("sandbox-parent-daily");
  await expect(panel).toBeVisible();
  await expect(page.getByTestId("parent-daily-child")).toHaveText("Jordan Reed");
  await expect(page.getByTestId("parent-daily-attendance")).toContainText("PRESENT");
  await expect(page.getByTestId("parent-daily-progress")).toContainText("First Week Reading Check");
  await expect(page.getByTestId("parent-daily-progress")).toContainText("Jordan is off to a strong start");
  await expect(page.getByTestId("parent-daily-communications")).toContainText("Jordan Reed - First Week Update");
  await expect(page.getByTestId("parent-daily-billing")).not.toContainText("Family balance: $0.00");
  await expect(page.getByTestId("parent-daily-billing")).toContainText("External provider enabled: false");
  await expect(page.getByTestId("parent-daily-staff-controls")).toContainText("grade-write=false");
  await expect(page.getByTestId("parent-daily-staff-controls")).toContainText("attendance-write=false");
  await expect(page.getByTestId("parent-daily-staff-controls")).toContainText("admissions-decision=false");
  await expect(page.getByTestId("parent-daily-staff-controls")).toContainText("finance-admin=false");
  await expect(page.getByTestId("parent-daily-staff-controls")).toContainText("tenant-admin=false");

  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("parent-daily-child")).toHaveText("Jordan Reed");
  await expect(page.getByTestId("parent-daily-attendance")).toContainText("PRESENT");
  await expect(page.getByTestId("parent-daily-progress")).toContainText("First Week Reading Check");
  await expect(page.getByTestId("parent-daily-communications")).toContainText("Jordan Reed - First Week Update");
});
