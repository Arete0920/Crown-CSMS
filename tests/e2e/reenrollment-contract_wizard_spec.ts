import { expect, test } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Re-enrollment validates, selects seeded students, commits billing, and verifies persisted results', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/reenrollment`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /configure re-enrollment/i })).toBeVisible();

  await page.getByRole('button', { name: /continue/i }).click();
  await expect(page.locator('.crown-alert')).toContainText('Academic year label is required');

  await page.getByPlaceholder(/2026-2027/i).fill('2033-2034-E2E');
  await page.getByPlaceholder(/500\.00/i).fill('125.00');
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/reenrollment/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  const candidatesPromise = page.waitForResponse(r => r.url().includes('/candidates/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /continue/i }).click();
  const [createResponse, configureResponse, candidatesResponse] = await Promise.all([createPromise, configurePromise, candidatesPromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();
  expect(candidatesResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /review eligible students/i })).toBeVisible();
  const candidateData = await candidatesResponse.json();
  expect(candidateData.total).toBeGreaterThan(0);
  await page.getByRole('button', { name: /continue/i }).click();

  await expect(page.getByRole('heading', { name: /select students/i })).toBeVisible();
  const selectPromise = page.waitForResponse(r => r.url().includes('/select/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /continue with .* students/i }).click();
  const selectResponse = await selectPromise;
  expect(selectResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /preview re-enrollment/i })).toBeVisible();
  await expect(page.getByText('2033-2034-E2E')).toBeVisible();
  await page.getByRole('button', { name: /proceed to commit/i }).click();

  await expect(page.getByRole('heading', { name: /commit re-enrollment/i })).toBeVisible();
  await page.getByText(/i have reviewed the preview/i).click();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit re-enrollment/i }).click();
  const commitResponse = await commitPromise;
  expect(commitResponse.ok()).toBeTruthy();
  await expect(page.getByText(/committed!/i)).toBeVisible();

  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /verify results/i }).click();
  const verifyResponse = await verifyPromise;
  expect(verifyResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /verify results/i })).toBeVisible();
  await expect(page.getByText(/re-enrollment complete/i)).toBeVisible();
  await expect(page.getByText('2033-2034-E2E')).toBeVisible();
  await expect(page.getByText(/billing run id/i)).not.toContainText('undefined');
});

test('Re-enrollment denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/reenrollment`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/reenrollment(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /configure re-enrollment/i })).toHaveCount(0);
});
