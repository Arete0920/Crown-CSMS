import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createSchedulingFixture, frontendUrl, launchHeritageRole, resultList } from './helpers/wizardCertification';

test('Section Assign persists a real Heritage roster mutation and verifies it', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/section-assign-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/section-assign-setup/);

  const fixture = await createSchedulingFixture(page, `ROSTER${Date.now().toString().slice(-6)}`);
  const studentsPayload = await authenticatedApiJson(page, '/api/v1/students/');
  const students = resultList(studentsPayload);
  const linkedStudent = students.find((row: any) => row.student_number === 'HCA-TCHR-001')
    || students.find((row: any) => row.student_number === 'HCA-TCHR-002');
  if (!linkedStudent) {
    throw new Error(`Heritage seed is missing the canonical/household linked teacher-roster student: ${JSON.stringify(studentsPayload)}`);
  }
  const studentId = String(linkedStudent.id);

  const created = await authenticatedApiJson(page, '/api/v1/section-assign-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: { section_id: fixture.sectionId, term: fixture.termCode || 'E2E' },
  });
  await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/load/`, {
    method: 'POST',
    body: { student_ids: [studentId] },
  });
  await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/stage/`, {
    method: 'POST',
    body: { changes: [{ student_id: studentId, action: 'add' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST',
    body: { confirm: true },
  });
  expect(committed.status).toBe('committed');
  expect(committed.enrolled).toBeGreaterThanOrEqual(1);

  const verified = await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/verify/`);
  expect(verified.status).toBe('verified');
  expect(verified.enrollment_count).toBeGreaterThanOrEqual(1);
});

test('Section Assign denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-assign-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-assign-setup(?:$|\?)/i);
});
