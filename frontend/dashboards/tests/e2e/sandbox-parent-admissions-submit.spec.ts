import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";
const seededParentEmail = "parent.reed@heritage.example.org";

async function openParentSandbox(page: Page) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("parent");
  const previewButton = page.getByRole("button", { name: /continue to heritage preview/i }).first();
  await expect(previewButton).toBeVisible();
  await previewButton.click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

async function advancePrefilledWizard(page: Page) {
  for (let step = 0; step < 2; step += 1) {
    const continueButton = page.getByRole("button", { name: /continue\s*->/i }).first();
    await expect(continueButton, `prefilled admissions step ${step + 1} must be complete`).toBeEnabled({ timeout: 15000 });
    await continueButton.click();
  }

  const guardianEmail = page.getByLabel("Email *").first();
  await expect(guardianEmail).toBeVisible({ timeout: 15000 });
  await guardianEmail.fill(seededParentEmail);

  for (let step = 0; step < 5; step += 1) {
    const continueButton = page.getByRole("button", { name: /continue\s*->/i }).first();
    await expect(continueButton, `prefilled admissions step ${step + 3} must be complete`).toBeEnabled({ timeout: 15000 });
    await continueButton.click();
  }

  const submitApplicationButton = page.getByRole("button", { name: /submit application\s*->/i }).first();
  await expect(submitApplicationButton).toBeEnabled({ timeout: 15000 });
  await submitApplicationButton.click();
}

test("sandbox parent admissions draft auto-saves, resumes, and completes document-readiness checklist", async ({ page }) => {
  await openParentSandbox(page);
  await page.goto(`${frontendUrl}/parent/admissions/start`, { waitUntil: "networkidle" });

  await page.getByRole("button", { name: /continue\s*->/i }).first().click();
  await page.getByRole("button", { name: /continue\s*->/i }).first().click();
  const guardianEmail = page.getByLabel("Email *").first();
  await guardianEmail.fill("resume-proof@heritage.example.org");

  await expect.poll(async () => page.evaluate(() => {
    const raw = localStorage.getItem("crown_wizard_draft:admissions-apply-demo");
    return raw ? JSON.parse(raw)?.value?.family?.guardians?.[0]?.email : "";
  })).toBe("resume-proof@heritage.example.org");

  await page.reload({ waitUntil: "networkidle" });
  await page.getByRole("button", { name: /continue\s*->/i }).first().click();
  await page.getByRole("button", { name: /continue\s*->/i }).first().click();
  await expect(page.getByLabel("Email *").first()).toHaveValue("resume-proof@heritage.example.org");

  // The current product supports document-readiness acknowledgements, not binary upload.
  // This proof certifies the implemented checklist rather than claiming upload support.
  await page.getByLabel("Email *").first().fill(seededParentEmail);
  for (let step = 0; step < 3; step += 1) {
    await page.getByRole("button", { name: /continue\s*->/i }).first().click();
  }
  await expect(page.getByText("Document Readiness", { exact: true })).toBeVisible();
  await expect(page.getByText("Ready items: 4/4", { exact: false })).toBeVisible();
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
  for (const label of ["Transcript available", "Recommendations available", "Pastor/church reference available", "Immunization records available"]) {
    await expect(page.getByLabel(label)).toBeChecked();
  }
});

test("sandbox parent submits a real application and sees that exact application in status", async ({ page }) => {
  await openParentSandbox(page);

  await page.goto(`${frontendUrl}/parent/admissions/start`, { waitUntil: "networkidle" });
  await expect(page.getByText("Heritage Christian Academy", { exact: false }).first()).toBeVisible();

  await advancePrefilledWizard(page);

  const feeAcknowledgement = page.getByLabel(/I acknowledge the application fee policy/i).first();
  if ((await feeAcknowledgement.count()) > 0 && !(await feeAcknowledgement.isChecked())) {
    await feeAcknowledgement.check();
  }

  const confirmButton = page.getByRole("button", { name: /^Confirm and Submit$/i }).first();
  await expect(confirmButton).toBeEnabled({ timeout: 30000 });

  const submissionResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/admissions/submit/") && response.request().method() === "POST",
    { timeout: 30000 },
  );
  const checklistNavigationPromise = page.waitForURL(
    (url) => Boolean(url.searchParams.get("application_id") && url.searchParams.get("checklist_key")),
    { timeout: 30000 },
  );

  await confirmButton.click();
  const submissionResponse = await submissionResponsePromise;
  expect(submissionResponse.ok(), `admissions submit returned ${submissionResponse.status()}`).toBeTruthy();

  await checklistNavigationPromise;
  const checklistUrl = new URL(page.url());
  const applicationId = checklistUrl.searchParams.get("application_id") || "";
  const checklistKey = checklistUrl.searchParams.get("checklist_key") || "";
  expect(applicationId.length, "submission redirect must identify the persisted application").toBeGreaterThan(0);
  expect(checklistKey.length, "submission redirect must identify the persisted checklist").toBeGreaterThan(0);
  expect(checklistUrl.searchParams.get("demo_flow"), "sandbox submission must remain in demo flow").toBe("1");

  const overviewResponsePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/parent360/me/overview/") && response.request().method() === "GET",
    { timeout: 30000 },
  );
  await page.goto(`${frontendUrl}/parent/admissions/status`, { waitUntil: "domcontentloaded" });
  const overviewResponse = await overviewResponsePromise;
  expect(overviewResponse.ok(), `Parent360 status contract returned ${overviewResponse.status()}`).toBeTruthy();

  const overview = await overviewResponse.json();
  const surfacedIds = Array.isArray(overview?.admissions_continuity?.applications)
    ? overview.admissions_continuity.applications.map((application: { application_id?: string }) => String(application?.application_id || ""))
    : [];
  expect(surfacedIds, "Parent360 must surface the exact application created in this transaction").toContain(applicationId);

  await expect(page).toHaveURL(/\/parent\/admissions\/status/);
  await expect(page.getByTestId("parent-journey-status")).toBeVisible({ timeout: 30000 });
  await expect(page.getByText(/service unavailable|access denied|failed to load/i)).toHaveCount(0);
});
