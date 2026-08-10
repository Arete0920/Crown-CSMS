import { expect, test } from "@playwright/test";

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

test("sandbox teacher links and reopens a persisted curriculum resource", async ({ page }) => {
  await openTeacherSandbox(page);
  await page.goto(`${frontendUrl}/teacher/lesson-plans/today`, { waitUntil: "networkidle" });
  await expect(page.getByTestId("teacher-lesson-plan-editor")).toBeVisible();
  const sectionSelect = page.getByLabel("Lesson plan section");
  await expect(sectionSelect.locator("option")).toHaveCount(2, { timeout: 30000 });
  await sectionSelect.selectOption({ index: 1 });
  const unitSelect = page.getByLabel("Curriculum unit");
  await expect(unitSelect.locator("option")).toHaveCount(2, { timeout: 30000 });
  await unitSelect.selectOption({ index: 1 });
  const lessonSelect = page.getByLabel("Curriculum lesson");
  await expect(lessonSelect.locator("option")).toHaveCount(2, { timeout: 30000 });
  await lessonSelect.selectOption({ index: 1 });
  const marker = `Heritage curriculum proof ${Date.now()}`;
  const resourceUrl = "https://example.org/heritage/grade-5-english";
  await page.getByLabel("Curriculum resource title").fill(marker);
  await page.getByLabel("Curriculum resource link").fill(resourceUrl);
  const postResponse = page.waitForResponse((response) => response.request().method() === "POST" && /\/api\/v1\/academics\/lessons\/[^/]+\/resources\/$/.test(new URL(response.url()).pathname));
  await page.getByRole("button", { name: /add curriculum resource/i }).click();
  const created = await postResponse;
  expect(created.status()).toBe(201);
  const resourceStatus = page.getByRole("status").filter({ hasText: /curriculum resource/i });
  await expect(resourceStatus).toContainText(/curriculum resource saved/i, { timeout: 30000 });
  await expect(page.getByRole("link", { name: /open resource/i })).toHaveAttribute("href", resourceUrl);
  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByText(marker, { exact: true })).toBeVisible({ timeout: 30000 });
  await expect(page.getByRole("link", { name: /open resource/i })).toHaveAttribute("href", resourceUrl);
});
