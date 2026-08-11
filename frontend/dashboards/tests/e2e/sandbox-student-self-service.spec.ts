import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

async function openStudentSandbox(page: Page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("student");
  await page.getByRole("button", { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test("sandbox student reviews schedule assignments progress attendance and communications", async ({ page }) => {
  await openStudentSandbox(page);
  await page.goto(`${frontendUrl}/student`, { waitUntil: "domcontentloaded" });

  const panel = page.getByTestId("sandbox-student-self-service");
  await expect(panel).toBeVisible();
  await expect(page.getByTestId("student-self-service-name")).toHaveText("Avery Reed");
  await expect(page.getByTestId("student-schedule")).toContainText("Grade 7 English Language Arts");
  await expect(page.getByTestId("student-learning-tasks")).toContainText("Summer Reading Reflection");
  await expect(page.getByTestId("student-attendance")).toContainText("PRESENT");
  await expect(page.getByTestId("student-communications")).toContainText("Grade 7 Welcome and First Week");
  await expect(page.getByTestId("student-privilege-boundary")).toContainText("grading=false");
  await expect(page.getByTestId("student-privilege-boundary")).toContainText("admissions=false");
  await expect(page.getByTestId("student-privilege-boundary")).toContainText("finance=false");
  await expect(page.getByTestId("student-privilege-boundary")).toContainText("tenant-admin=false");

  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("student-schedule")).toContainText("Grade 7 English Language Arts");
  await expect(page.getByTestId("student-learning-tasks")).toContainText("Vocabulary Check 1");

  for (const forbidden of ["/gradebook", "/admissions", "/finance", "/school-admin-dashboard"]) {
    await page.goto(`${frontendUrl}${forbidden}`, { waitUntil: "domcontentloaded" });
    await expect(page).not.toHaveURL(new RegExp(`${forbidden.replaceAll("/", "\\/")}(?:$|\\?)`));
  }
});
