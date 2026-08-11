import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";
const targetFamily = "Mercer Enrollment Conversion Demo Family";

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

test("Admissions Director converts a canonical-ready accepted applicant from the visible pipeline", async ({ page }) => {
  await openAdmissionsSandbox(page);
  const listPromise = page.waitForResponse((response) => response.url().includes("/admissions/applications/") && response.request().method() === "GET", { timeout: 30000 });
  await page.goto(`${frontendUrl}/admissions/pipeline`, { waitUntil: "domcontentloaded" });
  const listResponse = await listPromise; expect(listResponse.ok(), `applications list returned ${listResponse.status()}`).toBeTruthy();
  const applications = await listResponse.json();
  const target = applications.find((row: any) => (row.household_name === targetFamily || row.applicant_name === targetFamily) && row.status === "ACCEPTED");
  expect(target, "deterministic enrollment-ready accepted applicant must exist").toBeTruthy();
  const row = page.getByRole("row").filter({ hasText: targetFamily }).filter({ hasText: "Accepted" }).first();
  await expect(row).toBeVisible(); await row.getByRole("button", { name: "Open" }).click(); await expect(page.getByText("Household Admissions Review")).toBeVisible(); await page.getByRole("button", { name: "Show details" }).first().click();
  const enrollPromise = page.waitForResponse((response) => response.url().includes("/api/admissions/enroll/") && response.request().method() === "POST", { timeout: 30000 });
  await page.getByRole("button", { name: "Enroll Child" }).first().click();
  const enrollResponse = await enrollPromise; expect(enrollResponse.status(), "canonical enrollment POST must succeed").toBe(200);
  const enrollment = await enrollResponse.json(); expect(enrollment.ok).toBe(true); expect(enrollment.already_enrolled).toBe(false); expect(enrollment.student_id).toBeTruthy(); expect(enrollment.canonical_application_id).toBeTruthy(); expect(enrollment.canonical_gate).toBe("contract_countersigned_and_deposit_paid_or_waived");
  await expect(page.getByRole("alert").filter({ hasText: /Enrolled successfully/i })).toBeVisible();
  await page.reload({ waitUntil: "networkidle" });
  const enrolledRow = page.getByRole("row").filter({ hasText: targetFamily }).filter({ hasText: "Enrolled" }).first();
  await expect(enrolledRow).toBeVisible(); await enrolledRow.getByRole("button", { name: "Open" }).click(); await page.getByRole("button", { name: "Show details" }).first().click(); await expect(page.getByRole("button", { name: "Enrolled" }).first()).toBeDisabled();
});
