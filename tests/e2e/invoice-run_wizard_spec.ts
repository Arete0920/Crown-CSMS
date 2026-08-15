import { expect, test } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Invoice Run wizard loads obligations, commits invoices, and verifies live backend state', async ({ page }) => {
  await launchHeritageRole(page, 'finance_director');
  await page.goto(`${frontendUrl}/invoice-run`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /configure period/i })).toBeVisible();

  await page.locator('input[type="date"]').nth(0).fill('2032-09-01');
  await page.locator('input[type="date"]').nth(1).fill('2032-09-30');
  await page.locator('input[type="date"]').nth(2).fill('2032-10-15');
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/invoice-run-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Next' }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /load obligations/i })).toBeVisible();
  const loadPromise = page.waitForResponse(r => r.url().includes('/load/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /load open obligations/i }).click();
  expect((await loadPromise).ok()).toBeTruthy();
  await expect(page.getByText(/open obligation\(s\)/i)).toBeVisible();
  await page.getByRole('button', { name: 'Next' }).click();

  await expect(page.getByRole('heading', { name: 'Preview' })).toBeVisible();
  await expect(page.getByText('2032-10-15')).toBeVisible();
  await page.getByRole('button', { name: /confirm & commit/i }).click();

  await expect(page.getByRole('heading', { name: 'Commit' })).toBeVisible();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /generate invoices/i }).click();
  const commitResponse = await commitPromise;
  expect(commitResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Verify' })).toBeVisible();
  await expect(page.locator('.crown-success-box')).toContainText('2032-09-01', { timeout: 30000 });
  await expect(page.locator('.crown-success-box')).toContainText('2032-09-30');
  await expect(page.locator('.crown-success-box')).toContainText(/status:/i);
});

test('Invoice Run wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/invoice-run`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/invoice-run(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /configure period/i })).toHaveCount(0);
});
