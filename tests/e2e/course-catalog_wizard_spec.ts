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

test('Course Catalog wizard persists a live catalog commit', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/course-catalog-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /course catalog/i })).toBeVisible();
  await page.locator('input[placeholder="Code (e.g. ENG1)"]').fill('E2E-ENG7');
  await page.locator('input[placeholder="Name"]').fill('E2E Grade 7 English');
  await page.locator('input[placeholder="Credits"]').fill('1');

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/course-catalog-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit catalog/i }).click();
  const [createResponse, configureResponse, commitResponse] = await Promise.all([createPromise, configurePromise, commitPromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();
  expect(commitResponse.ok()).toBeTruthy();
  await expect(page.getByRole('heading', { name: 'Done' })).toBeVisible();
  await expect(page.getByText(/total:/i)).not.toContainText('undefined');
});

test('Course Catalog wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/course-catalog-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/course-catalog-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /course catalog/i })).toHaveCount(0);
});