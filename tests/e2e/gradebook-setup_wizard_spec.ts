import { expect, test } from '@playwright/test';
import { createSchedulingSectionFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Gradebook Setup persists and verifies weighted categories for a live section', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const section = await createSchedulingSectionFixture(page, 'GRADE');

  await page.goto(`${frontendUrl}/gradebook-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /select section/i })).toBeVisible();
  await page.getByPlaceholder('00000000-0000-0000-0000-000000000000').fill(section.sectionId);

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/gradebook-setup-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /^next$/i }).click();
  expect((await createPromise).ok()).toBeTruthy();
  expect((await configurePromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /define categories/i })).toBeVisible();
  await page.getByPlaceholder('Name').fill('Assignments E2E');
  await page.getByPlaceholder('Weight %').fill('100');
  const categoriesPromise = page.waitForResponse(r => r.url().includes('/categories/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /^next$/i }).click();
  expect((await categoriesPromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /^preview$/i })).toBeVisible();
  await expect(page.getByText('Assignments E2E', { exact: true })).toBeVisible();
  await expect(page.getByText('100%', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /confirm & commit/i }).click();

  await expect(page.getByRole('heading', { name: /^commit$/i })).toBeVisible();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /^commit$/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();
  const verified = await verifyResponse.json();
  expect(verified.section_id).toBe(section.sectionId);
  expect(verified.category_count).toBeGreaterThanOrEqual(1);

  await expect(page.getByRole('heading', { name: /^verify$/i })).toBeVisible();
  await expect(page.locator('.crown-success-box')).toContainText('categories saved');
  await expect(page.locator('.crown-success-box')).toContainText(section.sectionId);
});

test('Gradebook Setup denies an unauthorized Heritage Teacher without configure rights', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/gradebook-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/gradebook-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /select section/i })).toHaveCount(0);
});
