import { expect, test } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Enrollment Conversion validates, loads, commits, and verifies against the live backend', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/enrollment-conversion`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /configure/i })).toBeVisible();

  await page.getByRole('button', { name: 'Next' }).click();
  await expect(page.locator('.crown-error')).toContainText('Academic year label is required');

  // The disposable Heritage seed has one canonically ready ACCEPTED application
  // in 2026-2027. A fabricated empty year must not produce a successful commit.
  await page.getByPlaceholder(/2026-2027/i).fill('2026-2027');
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/enrollment-conversion-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Next' }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /load applicants/i })).toBeVisible();
  const loadPromise = page.waitForResponse(r => r.url().includes('/load/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /load applicants/i }).click();
  const loadResponse = await loadPromise;
  expect(loadResponse.ok()).toBeTruthy();
  expect((await loadResponse.json()).applicant_count).toBe(1);
  await expect(page.getByText(/applicant\(s\) to convert/i)).toBeVisible();
  await page.getByRole('button', { name: 'Next' }).click();

  await expect(page.getByRole('heading', { name: /preview/i })).toBeVisible();
  await page.getByRole('button', { name: /confirm.*commit/i }).click();
  await expect(page.getByRole('heading', { name: /commit/i })).toBeVisible();

  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /enroll now/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();
  const commitReceipt = await commitResponse.json();
  expect(commitReceipt.selected).toBe(1);
  expect(commitReceipt.converted).toBe(1);
  const verifyReceipt = await verifyResponse.json();
  expect(verifyReceipt.enrolled_count).toBe(1);
  expect(verifyReceipt.all_enrolled).toBe(true);

  await expect(page.getByRole('heading', { name: /verify/i })).toBeVisible();
  await expect(page.locator('.crown-success-box')).toContainText('2026-2027');
  await expect(page.locator('.crown-success-box')).toContainText('1 applicant(s) enrolled');
  await expect(page.locator('.crown-success-box')).toContainText(/status/i);
});

test('Enrollment Conversion denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/enrollment-conversion`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/enrollment-conversion(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /configure/i })).toHaveCount(0);
});
