import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";
const intakePath = "/api/v1/aid/family/demo-intake/";

async function signInFictionalParent(page: Page) {
  await page.goto(frontendUrl + "/login", { waitUntil: "networkidle" });
  const roleSelect = page.locator("#login-role").first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption("parent");
  await page.getByRole("button", { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test("local fictional family submits canonical school aid and reads persisted status after reload", async ({ page }) => {
  await signInFictionalParent(page);
  await page.goto(frontendUrl + "/parent/financial-aid", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Family Financial Aid demonstration" })).toBeVisible();
  const intakeResponse = page.waitForResponse(
    (response) => response.url().includes(intakePath) && response.request().method() === "GET",
  );
  await page.getByRole("button", { name: "Refresh saved status" }).click();
  const before = await intakeResponse;
  expect(before.ok()).toBe(true);
  const source = await before.json();
  expect(source.demo_only).toBe(true);
  expect(source.students.length).toBeGreaterThan(0);
  expect(source.academic_years.length).toBeGreaterThan(0);

  // This acceptance spec MUST exercise a new POST, not silently pass when
  // old fictional records are already present. Rehearse from a clean local
  // database; existing application readback has separate backend coverage.
  expect(
    source.applications.some(
      (item: { academic_year_id: string }) =>
        String(item.academic_year_id) === String(source.academic_years[0].id)
    ),
    "Fresh isolated buyer rehearsal must begin without this family's aid application",
  ).toBe(false);

  const firstStudent = source.students[0] as { id: string; name: string };
  await page.getByLabel(firstStudent.name).check();
  await page.getByLabel("Fictional household size").fill("3");
  await page.getByLabel("Fictional financial scenario").selectOption("fictional_modest");
  await page.getByLabel(/I confirm all application information is fictional/i).check();

  const posted = page.waitForResponse(
    (response) => response.url().includes(intakePath) && response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Submit fictional Financial Aid application" }).click();
  const submission = await posted;
  expect(submission.status()).toBe(201);
  const created = await submission.json();
  const applicationId = created.application.id;
  expect(applicationId).toBeTruthy();
  await expect(page.getByTestId("jireh-submit-confirmation")).toContainText(String(applicationId));
  await expect(page.getByTestId("jireh-saved-applications")).toContainText("SUBMITTED");

  await page.reload({ waitUntil: "networkidle" });
  await expect(page.getByTestId("jireh-saved-applications")).toContainText(String(applicationId));
  await expect(page.getByTestId("jireh-saved-applications")).toContainText("SUBMITTED");
  await expect(page.getByText(/duplicate submission is disabled/i)).toBeVisible();
});

test("parent aid form blocks unconfirmed submit and hides actual financial input fields", async ({ page }) => {
  await signInFictionalParent(page);
  await page.goto(frontendUrl + "/parent/financial-aid", { waitUntil: "networkidle" });
  await expect(page.getByRole("heading", { name: "Family Financial Aid demonstration" })).toBeVisible();
  await expect(page.getByText(/never enter actual income/i)).toBeVisible();
  const existing = await page.getByText(/duplicate submission is disabled/i).count();
  if (existing === 0) {
    await expect(page.getByRole("button", { name: "Submit fictional Financial Aid application" })).toBeDisabled();
  }
  await expect(page.getByLabel("Fictional financial scenario")).toBeVisible();
  await expect(page.locator('input[name="actual_income"]')).toHaveCount(0);
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
});
