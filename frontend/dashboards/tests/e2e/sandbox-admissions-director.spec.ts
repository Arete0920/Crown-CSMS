import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

async function openAdmissionsSandbox(page: Page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("admissions_director");
  const previewButton = page.getByRole("button", { name: /continue to heritage preview/i }).first();
  await expect(previewButton).toBeVisible();
  await previewButton.click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test("sandbox admissions director reviews and accepts a real applicant", async ({ page }) => {
  await openAdmissionsSandbox(page);

  const listPromise = page.waitForResponse(
    (response) => response.url().includes("/api/admissions/applications/") && response.request().method() === "GET",
    { timeout: 30000 },
  );
  await page.goto(`${frontendUrl}/admissions/pipeline`, { waitUntil: "domcontentloaded" });
  const listResponse = await listPromise;
  expect(listResponse.ok(), `applications list returned ${listResponse.status()}`).toBeTruthy();
  const applications = await listResponse.json();
  const target = applications.find((row: any) => row.applicant_name === "Carter Admissions Demo Family");
  expect(target, "deterministic admissions applicant must exist").toBeTruthy();
  expect(target.status).toBe("UNDER_REVIEW");
  expect(target.academic_year_id).toBeTruthy();

  const row = page.getByRole("row").filter({ hasText: "Carter Admissions Demo Family" });
  await expect(row).toBeVisible();
  await row.getByRole("button", { name: "Open" }).click();
  const drawer = page.getByTestId("admissions-household-review");
  await expect(drawer).toBeVisible();
  await drawer.getByRole("button", { name: "Show details" }).first().click();

  const decisionPromise = page.waitForResponse(
    (response) => response.url().includes("/api/admissions/decision/") && response.request().method() === "POST",
    { timeout: 30000 },
  );
  await drawer.getByRole("button", { name: "Accept" }).first().click();
  const decisionResponse = await decisionPromise;
  expect(decisionResponse.ok(), `decision returned ${decisionResponse.status()}`).toBeTruthy();
  const decisionPayload = await decisionResponse.json();
  expect(decisionPayload.status).toBe("ACCEPTED");
  await expect(drawer).toContainText("Accepted");

  await page.reload({ waitUntil: "networkidle" });
  const acceptedRow = page.getByRole("row").filter({ hasText: "Carter Admissions Demo Family" });
  await expect(acceptedRow).toContainText("Accepted");
});
