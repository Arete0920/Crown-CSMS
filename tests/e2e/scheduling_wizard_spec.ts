import { expect, test } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Scheduling Setup creates and verifies a real course and section in canonical scope', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const runId = `${Date.now()}`.slice(-7);
  const courseCode = `E2E${runId}`;
  const courseName = `E2E Scheduling ${runId}`;

  const scopePromise = page.waitForResponse(r => r.url().includes('/api/v1/scheduling-wizard/scope-options/') && r.request().method() === 'GET');
  await page.goto(`${frontendUrl}/scheduling-setup`, { waitUntil: 'networkidle' });
  const scopeResponse = await scopePromise;
  expect(scopeResponse.ok()).toBeTruthy();
  const scope = await scopeResponse.json();
  expect(scope.academic_years?.length).toBeGreaterThan(0);
  expect(scope.terms?.length).toBeGreaterThan(0);
  await expect(page.getByRole('heading', { name: /scheduling scope/i })).toBeVisible();

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/scheduling-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /continue/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.status()).toBe(201);
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /^courses$/i })).toBeVisible();
  await page.getByPlaceholder('MATH101').fill(courseCode);
  await page.getByPlaceholder('Algebra I').fill(courseName);
  await page.getByPlaceholder('Mathematics').fill('E2E Department');
  const coursesPromise = page.waitForResponse(r => r.url().includes('/courses/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /continue/i }).click();
  expect((await coursesPromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /^sections$/i })).toBeVisible();
  await page.locator('select').first().selectOption(courseCode);
  await page.getByPlaceholder('Mr. Smith').fill('E2E Teacher');
  await page.getByPlaceholder('9').fill('7');
  const sectionsPromise = page.waitForResponse(r => r.url().includes('/sections/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /continue/i }).click();
  expect((await sectionsPromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /^preview$/i })).toBeVisible();
  await expect(page.getByText(courseCode, { exact: true })).toBeVisible();
  await expect(page.getByText(courseName, { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /looks good.*commit/i }).click();

  await expect(page.getByRole('heading', { name: /^commit$/i })).toBeVisible();
  await page.getByText(/i confirm this scheduling setup/i).click();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /commit schedule/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();
  const verified = await verifyResponse.json();
  expect(verified.status).toBeTruthy();
  expect((verified.courses_created ?? 0) + (verified.courses_skipped ?? 0)).toBeGreaterThanOrEqual(1);
  expect((verified.sections_created ?? 0) + (verified.sections_skipped ?? 0)).toBeGreaterThanOrEqual(1);

  await expect(page.getByRole('heading', { name: /^verified$/i })).toBeVisible();
  await expect(page.getByText(/scheduling setup verified/i)).toBeVisible();
});

test('Scheduling Setup denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/scheduling-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/scheduling-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /scheduling scope/i })).toHaveCount(0);
});
