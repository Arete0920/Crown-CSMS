import { expect, test } from '@playwright/test';
import { createAcademicYearFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Bell Schedule wizard persists a canonical schedule for a live academic year', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  const academicYearId = await createAcademicYearFixture(page, 'BELL');
  await page.goto(`${frontendUrl}/bell-schedule-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /configure bell schedule/i })).toBeVisible();
  await page.getByPlaceholder(/standard, wed chapel, a-day/i).fill('E2E Standard Day');
  await page.getByPlaceholder(/uuid of the academic year/i).fill(academicYearId);
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/bell-schedule-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next: define period blocks/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();
  await page.getByPlaceholder('P1').fill('P1');
  await page.getByPlaceholder('Period 1').fill('Period 1 E2E');
  await page.locator('input[type="time"]').nth(0).fill('08:00');
  await page.locator('input[type="time"]').nth(1).fill('08:50');
  await page.locator('input[type="checkbox"]').first().check();
  const blocksPromise = page.waitForResponse(r => r.url().includes('/blocks/') && r.request().method() === 'POST');
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit bell schedule/i }).click();
  const [blocksResponse, commitResponse] = await Promise.all([blocksPromise, commitPromise]);
  expect(blocksResponse.ok()).toBeTruthy();
  expect(commitResponse.ok()).toBeTruthy();
  await expect(page.getByRole('heading', { name: /bell schedule committed/i })).toBeVisible();
  await expect(page.getByText('E2E Standard Day')).toBeVisible();
});

test('Bell Schedule wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/bell-schedule-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/bell-schedule-setup(?:$|\?)/i);
});
