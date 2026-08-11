import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

async function openTeacherSandbox(page: Page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("teacher");
  const previewButton = page.getByRole("button", { name: /continue to heritage preview/i }).first();
  await expect(previewButton).toBeVisible();
  await previewButton.click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test("sandbox teacher records attendance and creates persistent classwork", async ({ page }) => {
  await openTeacherSandbox(page);

  await page.goto(`${frontendUrl}/teacher/attendance`, { waitUntil: "networkidle" });
  const sectionSelect = page.getByLabel("Section:").or(page.locator("#teacher-attendance-section"));
  await expect(sectionSelect).toBeVisible();
  const options = await sectionSelect.locator("option").evaluateAll((rows) => rows.map((row) => ({ value: (row as HTMLOptionElement).value, text: row.textContent || "" })));
  const section = options.find((row) => row.value);
  expect(section?.value, "teacher sandbox must seed an assigned section").toBeTruthy();
  await sectionSelect.selectOption(section!.value);

  const statusSelects = page.locator("tbody select");
  await expect(statusSelects.first()).toBeVisible();
  expect(await statusSelects.count()).toBeGreaterThanOrEqual(2);
  await statusSelects.first().selectOption("absent");

  const attendancePost = page.waitForResponse(
    (response) => response.url().includes(`/api/v1/academics/sections/${section!.value}/attendance/`) && response.request().method() === "POST",
    { timeout: 30000 },
  );
  await page.getByRole("button", { name: /submit attendance/i }).click();
  const attendanceResponse = await attendancePost;
  expect(attendanceResponse.ok(), `attendance returned ${attendanceResponse.status()}`).toBeTruthy();
  const attendancePayload = await attendanceResponse.json();
  expect(Number(attendancePayload.created) + Number(attendancePayload.updated)).toBeGreaterThanOrEqual(2);
  await expect(page.getByText(/Saved: created=/i)).toBeVisible();

  await page.goto(`${frontendUrl}/teacher/classes`, { waitUntil: "networkidle" });
  const panel = page.getByTestId("teacher-classwork-panel");
  await expect(panel).toBeVisible();
  const assignmentName = `Owner Demo Classwork ${Date.now()}`;
  await panel.getByLabel("Assignment name").fill(assignmentName);
  await panel.getByLabel("Points possible").fill("15");

  const assignmentPost = page.waitForResponse(
    (response) => response.url().includes("/api/v1/academics/sections/") && response.url().includes("/assignments/") && response.request().method() === "POST",
    { timeout: 30000 },
  );
  await panel.getByRole("button", { name: /create assignment/i }).click();
  const assignmentResponse = await assignmentPost;
  expect(assignmentResponse.status()).toBe(201);
  const created = await assignmentResponse.json();
  expect(created.name).toBe(assignmentName);
  await expect(panel.getByRole("status")).toContainText(assignmentName);
  await expect(panel.getByText(assignmentName, { exact: true })).toBeVisible();

  await page.reload({ waitUntil: "networkidle" });
  const reloadedPanel = page.getByTestId("teacher-classwork-panel");
  await expect(reloadedPanel.getByText(assignmentName, { exact: true })).toBeVisible({ timeout: 30000 });
});
