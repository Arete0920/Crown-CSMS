import { expect, test } from '@playwright/test';
import { authenticatedApiJson, authenticatedCsvUpload, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

const headers = [
  'student_external_id','student_first_name','student_last_name','student_dob','grade_level','student_status',
  'guardian_external_id','guardian_first_name','guardian_last_name','guardian_email','guardian_relationship','household_external_id',
].join(',');

test('Onboarding imports a real household, guardian, and student and verifies the commit', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/onboarding`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/onboarding/);

  const suffix = Date.now().toString().slice(-8);
  const row = [
    `STU-${suffix}`,'E2E','Student','2014-01-15','7','ACTIVE',
    `GUA-${suffix}`,'E2E','Guardian',`guardian-${suffix}@school.test`,'parent',`HH-${suffix}`,
  ].join(',');
  const csv = `${headers}\n${row}\n`;

  const created = await authenticatedApiJson(page, '/api/v1/onboarding/imports/', { method: 'POST', body: { mode: 'students_guardians' } });
  const importId = created.import_id;
  expect(importId).toBeTruthy();
  const uploaded = await authenticatedCsvUpload(page, `/api/v1/onboarding/imports/${importId}/upload/`, csv, `onboarding-${suffix}.csv`);
  expect(uploaded.rows_total).toBe(1);
  const validated = await authenticatedApiJson(page, `/api/v1/onboarding/imports/${importId}/validate/`, { method: 'POST', body: {} });
  expect(validated.errors).toEqual([]);
  const preview = await authenticatedApiJson(page, `/api/v1/onboarding/imports/${importId}/preview/`);
  expect(preview.summary.students_to_create).toBe(1);
  expect(preview.summary.guardians_to_create).toBe(1);
  const committed = await authenticatedApiJson(page, `/api/v1/onboarding/imports/${importId}/commit/`, { method: 'POST', body: { confirm: true } });
  expect(committed.students_imported).toBe(1);
  expect(committed.guardians_imported).toBe(1);
  expect(committed.households_imported).toBe(1);
  expect(committed.exceptions_count).toBe(0);
  const verified = await authenticatedApiJson(page, `/api/v1/onboarding/imports/${importId}/verify/`);
  expect(verified.students_imported).toBe(1);
  expect(verified.guardians_imported).toBe(1);
  expect(verified.households_imported).toBe(1);
  expect(verified.exceptions_count).toBe(0);
  expect(verified.checks.every((check: any) => check.status === 'pass')).toBeTruthy();
});

test('Onboarding denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/onboarding`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/onboarding(?:$|\?)/i);
});
