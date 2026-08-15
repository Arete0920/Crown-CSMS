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

test('Billing Setup wizard validates, persists a plan, commits, and verifies against live API', async ({ page }) => {
  await launchHeritageRole(page, 'finance_director');
  await page.goto(`${frontendUrl}/billing-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /mode & term/i })).toBeVisible();

  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.locator('.crown-alert')).toContainText('Term is required');

  await page.locator('#billing-term').fill('2026-FALL-E2E');
  const createPromise = page.waitForResponse(
    (response) => response.url().includes('/api/v1/billing-wizard/sessions/') && response.request().method() === 'POST',
  );
  const configurePromise = page.waitForResponse(
    (response) => response.url().includes('/configure/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Continue' }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok(), `create returned ${createResponse.status()}`).toBeTruthy();
  expect(configureResponse.ok(), `configure returned ${configureResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /define tuition plans/i })).toBeVisible();
  await page.locator('#billing-plan-name-0').fill('Annual Tuition E2E');
  await page.locator('#billing-plan-amount-0').fill('12000');
  await page.locator('#billing-plan-installments-0').fill('2');
  await page.locator('#billing-plan-first-due-0').fill('2026-09-01');
  await page.locator('#billing-plan-cadence-0').fill('30');

  const plansPromise = page.waitForResponse(
    (response) => response.url().includes('/plans/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Continue' }).click();
  const plansResponse = await plansPromise;
  expect(plansResponse.ok(), `plans returned ${plansResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /define fees/i })).toBeVisible();
  const feesPromise = page.waitForResponse(
    (response) => response.url().includes('/fees/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: /no fees, skip/i }).click();
  const feesResponse = await feesPromise;
  expect(feesResponse.ok(), `fees returned ${feesResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /schedule preview/i })).toBeVisible();
  await expect(page.getByText('Annual Tuition E2E')).toBeVisible();
  await expect(page.getByText('$6,000.00')).toHaveCount(2);
  await page.getByRole('button', { name: /looks good.*commit/i }).click();

  await expect(page.getByRole('heading', { name: /commit billing setup/i })).toBeVisible();
  await page.getByText(/i confirm this billing setup/i).click();
  const commitPromise = page.waitForResponse(
    (response) => response.url().includes('/commit/') && response.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    (response) => response.url().includes('/verify/') && response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /commit billing setup/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Verified' })).toBeVisible();
  await expect(page.getByText(/billing setup verified/i)).toBeVisible();
  await expect(page.getByText('Annual Tuition E2E')).toBeVisible();
  await expect(page.getByText(/2026-FALL-E2E/)).toBeVisible();
});

test('Billing Setup wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/billing-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/billing-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /mode & term/i })).toHaveCount(0);
});
