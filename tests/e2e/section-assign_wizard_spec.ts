import { expect, test } from '@playwright/test';
import { createSchedulingSectionFixture, frontendUrl, getCanonicalStudentFixture, launchHeritageRole } from './helpers/wizardCertification';

test('Section Assign stages, commits, and verifies a live enrollment change', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const section = await createSchedulingSectionFixture(page, 'ASSIGN');
  const student = await getCanonicalStudentFixture(page);

  await page.goto(`${frontendUrl}/section-assign-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /section & term/i })).toBeVisible();
  await page.getByPlaceholder('00000000-0000-0000-0000-000000000000').fill(section.sectionId);

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/section-assign-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next/i }).click();
  expect((await createPromise).ok()).toBeTruthy();
  expect((await configurePromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /load students/i })).toBeVisible();
  await page.locator('textarea').fill(student.studentId);
  const loadPromise = page.waitForResponse(r => r.url().includes('/load/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next/i }).click();
  const loadResponse = await loadPromise;
  expect(loadResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /stage roster/i })).toBeVisible();
  await expect(page.getByText(student.studentId, { exact: true })).toBeVisible();
  const stagePromise = page.waitForResponse(r => r.url().includes('/stage/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next/i }).click();
  expect((await stagePromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /^preview$/i })).toBeVisible();
  await expect(page.getByText(student.studentId, { exact: true })).toBeVisible();
  await page.getByRole('button', { name: /commit/i }).click();

  await expect(page.getByRole('heading', { name: /^commit$/i })).toBeVisible();
  await page.getByText(/i confirm these enrollment changes/i).click();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /commit enrollments/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();
  const committed = await commitResponse.json();
  const verified = await verifyResponse.json();
  expect((committed.enrolled ?? 0) + (committed.skipped ?? 0)).toBeGreaterThanOrEqual(1);
  expect(verified.section_id).toBe(section.sectionId);
  expect(verified.enrollment_count).toBeGreaterThanOrEqual(1);

  await expect(page.getByRole('heading', { name: /^verified$/i })).toBeVisible();
  await expect(page.getByText(/section roster committed and verified/i)).toBeVisible();
});

test('Section Assign denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-assign-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-assign-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /section & term/i })).toHaveCount(0);
});
