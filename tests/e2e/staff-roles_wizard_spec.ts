import { expect, test, type Page } from '@playwright/test';

const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';

async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  await page.locator('#login-role').first().selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test('Staff & Roles wizard persists a live staff roster commit', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/staff-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /staff roster/i })).toBeVisible();

  await page.getByPlaceholder('Email').fill('wizard.e2e.staff@heritage.example.org');
  await page.getByPlaceholder('First name').fill('Wizard');
  await page.getByPlaceholder('Last name').fill('Verifier');
  const checkboxes = page.locator('input[type="checkbox"]');
  await checkboxes.nth(0).check();
  await checkboxes.nth(1).check();

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/staff-setup-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit staff/i }).click();
  const [createResponse, configureResponse, commitResponse] = await Promise.all([createPromise, configurePromise, commitPromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();
  expect(commitResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Done' })).toBeVisible();
  await expect(page.getByText(/total:/i)).not.toContainText('undefined');
});

test('Staff & Roles wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/staff-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/staff-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /staff roster/i })).toHaveCount(0);
});
