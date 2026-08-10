import { test, expect } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

async function openTeacherSandbox(page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("teacher");
  const previewButton = page.getByRole("button", { name: /continue to heritage preview/i }).first();
  await expect(previewButton).toBeVisible();
  await previewButton.click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test("sandbox teacher creates, saves, and reopens a persisted lesson plan", async ({ page }) => {
  await openTeacherSandbox(page);

  await page.goto(`${frontendUrl}/teacher/lesson-plans/today`, { waitUntil: "networkidle" });
  await expect(page.getByTestId("teacher-lesson-plan-editor")).toBeVisible();

  const sectionSelect = page.getByLabel("Lesson plan section");
  await expect(sectionSelect).toBeVisible();
  await expect(sectionSelect.locator("option")).toHaveCount(2, { timeout: 30000 });
  await sectionSelect.selectOption({ index: 1 });

  const marker = `Sandbox lesson proof ${Date.now()}`;
  await page.getByLabel("Learning objectives").fill(marker);
  await page.getByLabel("Materials and curriculum resources").fill("Heritage demo curriculum resource");
  await page.getByLabel("Instructional activities").fill("Guided reading and written response");
  await page.getByLabel("Homework").fill("Complete reflection paragraph");
  await page.getByLabel("Private teacher notes").fill("Browser persistence proof");

  await page.getByRole("button", { name: /save lesson plan/i }).click();
  await expect(page.getByRole("status")).toContainText(/lesson plan saved/i, { timeout: 30000 });

  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("teacher-lesson-plan-editor")).toBeVisible();
  await expect(page.getByLabel("Learning objectives")).toHaveValue(marker, { timeout: 30000 });
  await expect(page.getByLabel("Materials and curriculum resources")).toHaveValue("Heritage demo curriculum resource");
  await expect(page.getByLabel("Private teacher notes")).toHaveValue("Browser persistence proof");
});
