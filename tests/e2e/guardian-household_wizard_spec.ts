import { expect, test } from '@playwright/test';
import { authenticatedApiJson, frontendUrl, launchHeritageRole, resultList } from './helpers/wizardCertification';

test('Guardian Household persists canonical family and guardian data and verifies it', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/guardian-household-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/guardian-household-setup/);

  const studentsPayload = await authenticatedApiJson(page, '/api/v1/students/');
  const students = resultList(studentsPayload);
  if (!students.length) throw new Error(`Heritage seed has no canonical students: ${JSON.stringify(studentsPayload)}`);
  const studentId = String(students[0].id);
  const email = `guardian.cert.${Date.now()}@heritage.example.org`;

  const created = await authenticatedApiJson(page, '/api/v1/guardian-household-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: {
      household_data: {
        name: `Certification Family ${Date.now()}`,
        address: { street: '10 Certification Way', city: 'Fairview', state: 'PA', zip: '19000' },
      },
    },
  });
  await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/add_guardians/`, {
    method: 'POST',
    body: { guardian_data: [{ name: 'Casey Certification', email, phone: '555-0199', custody_type: 'primary' }] },
  });
  await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/link_students/`, {
    method: 'POST',
    body: { link_data: [{ student_id: studentId, relationship: 'parent' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  expect(committed.status).toBe('committed');
  expect(committed.canonical_model).toBe('core');
  expect(committed.student_ids).toContain(studentId);

  const verified = await authenticatedApiJson(page, `/api/v1/guardian-household-wizard/sessions/${sessionId}/verify/`);
  expect(verified.status).toBe('verified');
  expect(verified.family_id).toBeTruthy();
});

test('Guardian Household denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/guardian-household-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/guardian-household-setup(?:$|\?)/i);
});
