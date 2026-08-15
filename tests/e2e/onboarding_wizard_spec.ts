import { expect, test } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

const csv = [
  'student_external_id,student_first_name,student_last_name,student_dob,grade_level,student_status,guardian_external_id,guardian_first_name,guardian_last_name,guardian_email,guardian_relationship,household_external_id',
  'E2E-S001,John,Wizard,2010-05-12,5,active,E2E-G001,Jane,Wizard,jane.wizard@example.com,mother,E2E-H001',
  'E2E-S002,Alice,Proof,2011-03-22,4,active,E2E-G002,Bob,Proof,bob.proof@example.com,father,E2E-H002',
].join('\n');

test('Onboarding imports CSV through the live UI, persists records, and verifies the result', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/onboarding`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /choose import type/i })).toBeVisible();

  await page.getByRole('button', { name: /continue/i }).click();
  await expect(page.getByRole('heading', { name: /upload csv/i })).toBeVisible();

  await page.locator('input[type="file"]').setInputFiles({
    name: 'onboarding-e2e.csv',
    mimeType: 'text/csv',
    buffer: Buffer.from(csv, 'utf8'),
  });
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/onboarding/imports/') && !r.url().includes('/upload/') && r.request().method() === 'POST');
  const uploadPromise = page.waitForResponse(r => r.url().includes('/upload/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /^upload$/i }).click();
  const [createResponse, uploadResponse] = await Promise.all([createPromise, uploadPromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(uploadResponse.ok()).toBeTruthy();
  await expect(page.getByText(/uploaded:/i)).toContainText('2 rows');

  await page.getByRole('button', { name: /continue/i }).click();
  await expect(page.getByRole('heading', { name: /validate data/i })).toBeVisible();
  const validatePromise = page.waitForResponse(r => r.url().includes('/validate/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /^validate$/i }).click();
  expect((await validatePromise).ok()).toBeTruthy();
  await expect(page.getByText(/all rows valid/i)).toBeVisible();

  await page.getByRole('button', { name: /continue/i }).click();
  const previewResponse = await page.waitForResponse(r => r.url().includes('/preview/') && r.request().method() === 'GET');
  expect(previewResponse.ok()).toBeTruthy();
  await expect(page.getByRole('heading', { name: /^preview$/i })).toBeVisible();
  await expect(page.getByText('E2E-S001')).toBeVisible();

  await page.getByRole('button', { name: /continue/i }).click();
  await expect(page.getByRole('heading', { name: /commit import/i })).toBeVisible();
  await page.getByText(/i have reviewed the preview/i).click();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit import/i }).click();
  const commitResponse = await commitPromise;
  expect(commitResponse.ok()).toBeTruthy();
  const committed = await commitResponse.json();
  expect(committed.students_imported).toBe(2);
  expect(committed.guardians_imported).toBe(2);
  expect(committed.households_imported).toBe(2);
  await expect(page.getByText(/committed!/i)).toBeVisible();

  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /verify results/i }).click();
  const verifyResponse = await verifyPromise;
  expect(verifyResponse.ok()).toBeTruthy();
  const verified = await verifyResponse.json();
  expect(verified.students_imported).toBe(2);
  expect(verified.guardians_imported).toBe(2);
  expect(verified.households_imported).toBe(2);
  await expect(page.getByRole('heading', { name: /verify results/i })).toBeVisible();
});

test('Onboarding denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/onboarding`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/onboarding(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /choose import type/i })).toHaveCount(0);
});
