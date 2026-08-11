import { expect, test, type Page } from "@playwright/test";

const frontendUrl = process.env.CERT_FRONTEND_URL || "http://127.0.0.1:4173";

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

test("sandbox parent accepts enrollment and sees resulting student context", async ({ page }) => {
  await openParentSandbox(page);

  const overviewPromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/parent360/me/overview/") && response.request().method() === "GET",
    { timeout: 30000 },
  );
  const enrollmentStatePromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/sandbox/parent/enrollment/") && response.request().method() === "GET",
    { timeout: 30000 },
  );
  await page.goto(`${frontendUrl}/parent/admissions/status`, { waitUntil: "domcontentloaded" });

  const overviewResponse = await overviewPromise;
  expect(overviewResponse.ok(), `Parent360 returned ${overviewResponse.status()}`).toBeTruthy();
  const overviewBefore = await overviewResponse.json();
  const applicationsBefore = overviewBefore?.admissions_continuity?.applications || [];
  const accepted = applicationsBefore.find((row: any) => row?.lifecycle_stage === "accepted");
  expect(accepted, "seeded Parent360 contract must expose an accepted applicant").toBeTruthy();

  const enrollmentStateResponse = await enrollmentStatePromise;
  expect(enrollmentStateResponse.ok()).toBeTruthy();
  const enrollmentBefore = await enrollmentStateResponse.json();
  expect(enrollmentBefore.lifecycle_stage).toBe("accepted");
  expect(enrollmentBefore.contract_status).toBe("sent");
  expect(enrollmentBefore.deposit_status).toBe("invoiced");
  expect(enrollmentBefore.demo_payment_processed).toBe(false);

  const panel = page.getByTestId("sandbox-parent-enrollment-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toContainText("Jordan Reed");

  const agreement = page.getByLabel("Accept sandbox enrollment agreement");
  await agreement.check();

  const postPromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/sandbox/parent/enrollment/") && response.request().method() === "POST",
    { timeout: 30000 },
  );
  const refreshedOverviewPromise = page.waitForResponse(
    (response) => response.url().includes("/api/v1/parent360/me/overview/") && response.request().method() === "GET",
    { timeout: 30000 },
  );

  await page.getByRole("button", { name: /accept enrollment and complete demo handoff/i }).click();

  const postResponse = await postPromise;
  expect(postResponse.ok(), `enrollment POST returned ${postResponse.status()}`).toBeTruthy();
  const completed = await postResponse.json();
  expect(completed.lifecycle_stage).toBe("enrolled");
  expect(completed.contract_status).toBe("countersigned");
  expect(completed.deposit_status).toBe("paid");
  expect(completed.applicant_to_student_status).toBe("completed");
  expect(completed.classroom_readiness_status).toBe("completed");
  expect(completed.parent_portal_activation_status).toBe("completed");
  expect(completed.child_id).toBeTruthy();
  expect(completed.demo_payment_processed).toBe(false);

  const refreshedOverviewResponse = await refreshedOverviewPromise;
  expect(refreshedOverviewResponse.ok()).toBeTruthy();
  const overviewAfter = await refreshedOverviewResponse.json();
  const applicationsAfter = overviewAfter?.admissions_continuity?.applications || [];
  const sameApplication = applicationsAfter.find(
    (row: any) => String(row?.application_id) === String(completed.application_id),
  );
  expect(sameApplication?.lifecycle_stage).toBe("enrolled");
  expect(Number(overviewAfter?.children_count || 0)).toBeGreaterThan(0);

  await expect(page.getByTestId("sandbox-parent-enrollment-complete")).toContainText("Jordan Reed");
  await expect(page.getByRole("status")).toContainText(/Enrollment completed and verified in Parent360/i);
  await expect(page.getByText(/No external payment was processed/i)).toBeVisible();
});
