import { expect, test } from '@playwright/test';
import { authenticatedApiJson, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Guardian Household writes to the canonical core family and verifies it', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const adminState = await authenticatedApiJson(page, '/api/v1/sandbox/admin/state/');
  const studentId = adminState.student_id;
  expect(studentId).toBeTruthy();

  await page.goto(`${frontendUrl}/guardian-household-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/guardian-household-setup/);

  const created = await authenticatedApiJson(page, '/api/v1/guardian-household-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  const suffix = Date.now().toString().slice(-7);
  await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: { household_data: { name: `E2E Family ${suffix}`, address: { street: '10 E2E Way', city: 'Middletown', state: 'DE', zip: '19709' } } },
  });
  await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/add_guardians/`, {
    method: 'POST',
    body: { guardian_data: [{ name: 'E2E Guardian', email: `guardian-${suffix}@school.test`, phone: '302-555-0100', custody_type: 'primary' }] },
  });
  await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/link_students/`, {
    method: 'POST', body: { link_data: [{ student_id: studentId, relationship: 'parent' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  const verified = await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/verify/`);
  expect(committed.canonical_model).toBe('core');
  expect(committed.student_ids).toContain(studentId);
  expect(verified.status).toBe('verified');
  expect(verified.family_id).toBe(committed.family_id);
});

test('Guardian Household denies an unauthorized Heritage Parent', async ({ page }) => {
  await launchHeritageRole(page, 'parent');
  await page.goto(`${frontendUrl}/guardian-household-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/guardian-household-setup(?:$|\?)/i);
});
