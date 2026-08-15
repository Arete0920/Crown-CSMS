import { expect, test, type Page } from '@playwright/test';

const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';

async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  const roleSelect = page.locator('#login-role').first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test('Attendance Rules wizard validates, persists, commits, and verifies against live API', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/attendance-rules-setup`, { waitUntil: 'networkidle' });

  await expect(page.getByRole('heading', { name: /label & year/i })).toBeVisible();
  await page.getByRole('button', { name: 'Next' }).click();
  await expect(page.locator('.crown-error')).toContainText('Label is required');

  await page.locator('#attendance-rules-label').fill('Heritage 2026 Attendance');
  await page.locator('#attendance-rules-school-year').fill('2026-2027');

  const createPromise = page.waitForResponse(
    (response) => response.url().includes('/api/v1/attendance-rules-wizard/sessions/') && response.request().method() === 'POST',
  );
  const configurePromise = page.waitForResponse(
    (response) => response.url().includes('/configure/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Next' }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok(), `create returned ${createResponse.status()}`).toBeTruthy();
  expect(configureResponse.ok(), `configure returned ${configureResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /define codes/i })).toBeVisible();
  const codeInputs = page.locator('input[placeholder="CODE"]');
  const labelInputs = page.locator('input[placeholder="Label"]');
  await codeInputs.first().fill('a');
  await labelInputs.first().fill('Absent');
  await page.getByRole('button', { name: /add code/i }).click();
  await codeInputs.nth(1).fill('e');
  await labelInputs.nth(1).fill('Excused');
  await page.locator('input[type="checkbox"]').nth(2).check();

  const definePromise = page.waitForResponse(
    (response) => response.url().includes('/codes/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Next' }).click();
  const defineResponse = await definePromise;
  expect(defineResponse.ok(), `define codes returned ${defineResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Preview' })).toBeVisible();
  await expect(page.getByText('Heritage 2026 Attendance')).toBeVisible();
  await expect(page.getByText('2026-2027')).toBeVisible();
  await expect(page.getByText('A', { exact: true })).toBeVisible();
  await expect(page.getByText('E', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /confirm & commit/i }).click();

  await expect(page.getByRole('heading', { name: 'Commit' })).toBeVisible();
  const commitPromise = page.waitForResponse(
    (response) => response.url().includes('/commit/') && response.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    (response) => response.url().includes('/verify/') && response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: 'Commit' }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Verify' })).toBeVisible();
  await expect(page.locator('.crown-success-box')).toContainText('Heritage 2026 Attendance');
  await expect(page.locator('.crown-success-box')).toContainText('2');
  await expect(page.locator('.crown-success-box')).toContainText('2026-2027');
});

test('Attendance Rules wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/attendance-rules-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/attendance-rules-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /label & year/i })).toHaveCount(0);
});
