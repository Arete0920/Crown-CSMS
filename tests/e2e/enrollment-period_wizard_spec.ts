import { expect, test } from '@playwright/test';
import { createAcademicYearFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Enrollment Period wizard persists capacity targets and verifies committed state', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const academicYearId = await createAcademicYearFixture(page, 'ENROLL');
  await page.goto(`${frontendUrl}/enrollment-period-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /configure enrollment window/i })).toBeVisible();

  const inputs = page.locator('input');
  await page.getByPlaceholder(/uuid from wizard/i).fill(academicYearId);
  await inputs.filter({ has: page.locator('[type="date"]') });
  await page.locator('input[type="date"]').nth(0).fill('2032-09-01');
  await page.locator('input[type="date"]').nth(1).fill('2033-02-15');
  await page.locator('input[type="date"]').nth(2).fill('2033-01-15');
  await page.locator('input[type="checkbox"]').first().check();

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/enrollment-period-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next: set capacities/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /grade capacities/i })).toBeVisible();
  await page.locator('select').first().selectOption('7');
  await page.locator('input[type="number"]').first().fill('48');

  const capacitiesPromise = page.waitForResponse(r => r.url().includes('/capacities/') && r.request().method() === 'POST');
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /commit enrollment period/i }).click();
  const [capacitiesResponse, commitResponse, verifyResponse] = await Promise.all([capacitiesPromise, commitPromise, verifyPromise]);
  expect(capacitiesResponse.ok()).toBeTruthy();
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /enrollment period committed/i })).toBeVisible();
  await expect(page.getByText('2032-09-01')).toBeVisible();
  await expect(page.getByText('2033-02-15')).toBeVisible();
  await expect(page.getByText(/grades created/i)).not.toContainText('undefined');
});

test('Enrollment Period wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/enrollment-period-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/enrollment-period-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /configure enrollment window/i })).toHaveCount(0);
});
