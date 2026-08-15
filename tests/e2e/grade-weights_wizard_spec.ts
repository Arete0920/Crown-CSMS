import { expect, test } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Grade Weights wizard persists categories, commits, and verifies live state', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/grade-weights-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: 'Setup', exact: true })).toBeVisible();

  await page.getByPlaceholder('Marking period').fill('Q1-E2E');
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/grade-weights-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue' }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Rows' })).toBeVisible();
  const rows = [
    { name: 'Tests E2E', weight_pct: 60 },
    { name: 'Homework E2E', weight_pct: 40 },
  ];
  await page.locator('textarea').fill(JSON.stringify(rows));
  const stagePromise = page.waitForResponse(r => r.url().includes('/stage_categories/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue' }).click();
  expect((await stagePromise).ok()).toBeTruthy();

  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /commit and verify/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();
  await expect(page.locator('pre')).toContainText('Q1-E2E');
  await expect(page.locator('pre')).toContainText('Tests E2E');
  await expect(page.locator('pre')).toContainText('Homework E2E');
});

test('Grade Weights wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/grade-weights-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/grade-weights-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: 'Setup', exact: true })).toHaveCount(0);
});
