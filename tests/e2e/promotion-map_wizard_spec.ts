import { expect, test, type Page } from '@playwright/test';

const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';

async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  await page.locator('#login-role').first().selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test('Promotion Map wizard persists promotion rules through live commit', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/promotion-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /promotion rules/i })).toBeVisible();

  const selects = page.locator('select');
  await selects.nth(0).selectOption('7');
  await selects.nth(1).selectOption('8');
  await page.getByRole('button', { name: /add rule/i }).click();
  await selects.nth(2).selectOption('8');
  await selects.nth(3).selectOption('9');

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/promotion-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit promotion map/i }).click();
  const [createResponse, configureResponse, commitResponse] = await Promise.all([createPromise, configurePromise, commitPromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();
  expect(commitResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Done' })).toBeVisible();
  await expect(page.getByText(/total:/i)).not.toContainText('undefined');
});

test('Promotion Map wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/promotion-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/promotion-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /promotion rules/i })).toHaveCount(0);
});
