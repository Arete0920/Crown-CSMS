import { expect, test } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Student Intake uploads, validates, commits, persists, and verifies a real CSV import', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const runId = `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  const studentFirst = `Jordan${runId.slice(-6)}`;
  const guardianFirst = `Casey${runId.slice(-6)}`;
  const lastName = `Proof${runId.slice(-6)}`;
  const csv = [
    'student_external_id,student_first_name,student_last_name,student_dob,grade_level,student_status,guardian_external_id,guardian_first_name,guardian_last_name,guardian_email,guardian_relationship,household_external_id',
    `E2E-STU-${runId},${studentFirst},${lastName},2020-03-15,6,active,E2E-GUA-${runId},${guardianFirst},${lastName},casey.${runId}@example.test,parent,E2E-HH-${runId}`,
  ].join('\n');

  await page.goto(`${frontendUrl}/onboarding`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /choose import type/i })).toBeVisible();

  await page.getByRole('button', { name: /continue/i }).click();
  await expect(page.getByRole('heading', { name: /upload csv/i })).toBeVisible();

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/onboarding/imports/') && r.request().method() === 'POST' && !r.url().includes('/upload/'));
  const uploadPromise = page.waitForResponse(r => r.url().includes('/upload/') && r.request().method() === 'POST');
  await page.locator('input[type="file"]').setInputFiles({
    name: `crown-onboarding-${runId}.csv`,
    mimeType: 'text/csv',
    buffer: Buffer.from(csv),
  });
  await page.getByRole('button', { name: 'Upload' }).click();
  const [createResponse, uploadResponse] = await Promise.all([createPromise, uploadPromise]);
  expect(createResponse.status()).toBe(201);
  expect(uploadResponse.ok()).toBeTruthy();
  await expect(page.getByText(/uploaded:/i)).toContainText(`crown-onboarding-${runId}.csv`);
  await expect(page.getByText(/1 rows/i)).toBeVisible();

  await page.getByRole('button', { name: /continue/i }).click();
  await expect(page.getByRole('heading', { name: /validate data/i })).toBeVisible();
  const validatePromise = page.waitForResponse(r => r.url().includes('/validate/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Validate' }).click();
  const validateResponse = await validatePromise;
  expect(validateResponse.ok()).toBeTruthy();
  const validation = await validateResponse.json();
  expect(validation.errors).toHaveLength(0);
  expect(validation.students_detected).toBe(1);
  expect(validation.guardians_detected).toBe(1);
  expect(validation.households_detected).toBe(1);
  await expect(page.getByText(/all rows valid/i)).toBeVisible();

  const previewPromise = page.waitForResponse(r => r.url().includes('/preview/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /continue/i }).click();
  const previewResponse = await previewPromise;
  expect(previewResponse.ok()).toBeTruthy();
  await expect(page.getByRole('heading', { name: /^preview$/i })).toBeVisible();
  await expect(page.getByText(studentFirst, { exact: true })).toBeVisible();
  await expect(page.getByText(lastName, { exact: true }).first()).toBeVisible();

  await page.getByRole('button', { name: /continue/i }).click();
  await expect(page.getByRole('heading', { name: /commit import/i })).toBeVisible();
  await page.getByText(/i have reviewed the preview and confirm this import/i).click();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit import/i }).click();
  const commitResponse = await commitPromise;
  expect(commitResponse.ok()).toBeTruthy();
  const committed = await commitResponse.json();
  expect(committed.exceptions_count).toBe(0);
  expect(committed.students_imported).toBe(1);
  expect(committed.guardians_imported).toBe(1);
  expect(committed.households_imported).toBe(1);
  await expect(page.getByText(/committed!/i)).toBeVisible();

  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /verify results/i }).click();
  const verifyResponse = await verifyPromise;
  expect(verifyResponse.ok()).toBeTruthy();
  const verified = await verifyResponse.json();
  expect(verified.students_imported).toBe(1);
  expect(verified.guardians_imported).toBe(1);
  expect(verified.households_imported).toBe(1);
  expect(verified.exceptions_count).toBe(0);
  expect(verified.checks.every((check: { status: string }) => check.status === 'pass')).toBeTruthy();
  await expect(page.getByRole('heading', { name: /verify results/i })).toBeVisible();
  await expect(page.getByText(/import session status/i)).toBeVisible();
});

test('Student Intake denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/onboarding`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/onboarding(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /choose import type/i })).toHaveCount(0);
});
