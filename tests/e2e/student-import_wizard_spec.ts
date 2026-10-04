import { expect, test } from '@playwright/test';
import { authenticatedApiJson, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Student Import reviews, commits, and verifies a live canonical student and identity link', async ({ page }) => {
  const familyId = process.env.CROWN_IMPORT_E2E_FAMILY_ID;
  const householdId = process.env.CROWN_IMPORT_E2E_HOUSEHOLD_ID;
  if (!familyId || !householdId) throw new Error('Seed the synthetic existing-school family/household bridge before canonical import certification.');
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/student-import-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: 'Configure school source data' })).toBeVisible();
  const studentNumber = `e2e-student-${Date.now()}`;
  const reason = 'Reviewed synthetic browser source and explicit school identity mapping';
  await page.getByLabel('Staged source rows').fill(JSON.stringify([
    { StudentNumber: studentNumber, FirstName: 'E2E', LastName: 'Student', BirthDate: '2014-01-01',
      Status: 'ACTIVE', FamilyId: familyId, HouseholdId: householdId, Grade: '' },
  ], null, 2));
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/student-import-wizard/sessions/') && r.request().method() === 'POST' && !r.url().includes('/configure/'));
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Configure import', exact: true }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();
  const { session_id: sessionId } = await createResponse.json();
  await expect(page.getByRole('heading', { name: 'Preview every proposed change' })).toBeVisible();
  const previewPromise = page.waitForResponse(r => r.url().includes('/preview/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Run canonical preview', exact: true }).click();
  const previewResponse = await previewPromise;
  expect(previewResponse.ok()).toBeTruthy();
  const preview = await previewResponse.json();
  expect(preview.schema).toBe(2);
  expect(preview.valid).toBe(1);
  expect(preview.errors).toEqual([]);
  expect(preview.rows).toHaveLength(1);
  expect(preview.rows[0].after.student_number).toBe(studentNumber);
  expect(preview.rows[0].after.family_id).toBe(familyId);
  expect(preview.rows[0].household_id).toBe(householdId);
  expect(preview.fingerprint).toBeTruthy();
  await expect(page.getByRole('heading', { name: 'Review before committing' })).toBeVisible();
  const commitButton = page.getByRole('button', { name: 'Commit reviewed batch and verify', exact: true });
  await expect(commitButton).toBeDisabled();
  await page.locator('summary').filter({ hasText: studentNumber }).click();
  await expect(page.getByText('After:', { exact: false })).toContainText(studentNumber);
  await page.getByLabel('Import review reason').fill(reason);
  await expect(commitButton).toBeDisabled();
  await page.getByRole('checkbox', { name: 'I reviewed every proposed change and its identity mappings' }).check();
  await expect(commitButton).toBeEnabled();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await commitButton.click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.request().postDataJSON()).toEqual({ confirm: true, fingerprint: preview.fingerprint, reason });
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();
  const committed = await commitResponse.json();
  const verified = await verifyResponse.json();
  expect(committed.created).toBe(1);
  expect(verified).toMatchObject({ session_id: sessionId, schema: 2, source: 'live', verified: true, verified_count: 1, differences: [] });
  expect(verified.records).toHaveLength(1);
  const record = verified.records[0];
  expect(record.after).toMatchObject({ student_number: studentNumber, first_name: 'E2E', last_name: 'Student', dob: '2014-01-01', status: 'ACTIVE', family_id: familyId });
  expect(record.household_id).toBe(householdId);
  expect(record.student_id).toBeTruthy();
  expect(record.compatibility_student_id).toBeTruthy();
  expect(record.identity_link_id).toBeTruthy();
  const compatibility = await authenticatedApiJson(page, `/api/v1/students/${record.compatibility_student_id}/`);
  expect(compatibility).toMatchObject({ id: record.compatibility_student_id, household: householdId, first_name: 'E2E', last_name: 'Student', is_active: true });
  await expect(page.getByRole('alert')).toHaveText('Canonical import verified');
  await expect(page.getByText('1 created · 0 updated · 1 verified against saved canonical records.', { exact: true })).toBeVisible();
});

test('Student Import wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/student-import-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/student-import-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: 'Configure school source data' })).toHaveCount(0);
});
