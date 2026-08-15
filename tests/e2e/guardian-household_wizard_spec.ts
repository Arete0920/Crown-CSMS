import { expect, test } from '@playwright/test';
import {
  authenticatedApiJson,
  frontendUrl,
  getCanonicalStudentFixture,
  launchHeritageRole,
} from './helpers/wizardCertification';

test('Guardian & Household creates, links, commits, and verifies canonical household records', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const { studentId } = await getCanonicalStudentFixture(page);
  const runId = `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;
  const base = '/api/v1/guardian-household-wizard/sessions/';

  const created = await authenticatedApiJson(page, base, { method: 'POST' });
  expect(created.session_id).toBeTruthy();
  const sessionId = created.session_id;

  const configured = await authenticatedApiJson(page, `${base}${sessionId}/configure/`, {
    method: 'POST',
    body: {
      household_data: {
        name: `E2E Household ${runId}`,
        address: { street: '101 Proof Way', city: 'Dallas', state: 'TX', postal_code: '75001' },
      },
    },
  });
  expect(configured.status).toBe('household_configured');

  const guardians = await authenticatedApiJson(page, `${base}${sessionId}/add_guardians/`, {
    method: 'POST',
    body: {
      guardian_data: [{
        name: `E2E Guardian ${runId}`,
        email: `guardian.${runId}@example.test`,
        custody_type: 'primary',
        contact_priority: 1,
        receives_communications: true,
      }],
    },
  });
  expect(guardians.status).toBe('guardians_added');
  expect(guardians.guardian_count).toBe(1);

  const linked = await authenticatedApiJson(page, `${base}${sessionId}/link_students/`, {
    method: 'POST',
    body: { link_data: [{ student_id: studentId, relationship: 'parent' }] },
  });
  expect(linked.status).toBe('students_linked');
  expect(linked.link_count).toBe(1);

  const committed = await authenticatedApiJson(page, `${base}${sessionId}/commit/`, {
    method: 'POST',
    body: { confirm: true },
  });
  expect(committed.status).toBe('committed');
  expect(committed.household_id).toBeTruthy();
  expect(committed.guardians_created).toBe(1);
  expect(committed.students_linked).toBe(1);

  const verified = await authenticatedApiJson(page, `${base}${sessionId}/verify/`);
  expect(verified.status).toBe('verified');
  expect(verified.household_id).toBe(committed.household_id);
  expect(verified.guardians_created).toBe(1);
  expect(verified.students_linked).toBe(1);
});

test('Guardian & Household denies an unauthorized Heritage Teacher route', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/guardian-household-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/guardian-household-setup(?:$|\?)/i);
  await expect(page.getByText(/guardian & household setup/i)).toHaveCount(0);
});
