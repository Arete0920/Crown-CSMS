import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createSchedulingFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Section Staffing persists a canonical TeacherAssignment and verifies it', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/section-staffing-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/section-staffing-setup/);

  const fixture = await createSchedulingFixture(page, `STAFF${Date.now().toString().slice(-6)}`);
  const staffSession = await authenticatedApiJson(page, '/api/v1/staff-onboarding-wizard/sessions/', { method: 'POST' });
  const staffSessionId = staffSession.session_id;
  const email = `wizard.staff.${Date.now()}@heritage.example.org`;
  await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${staffSessionId}/configure/`, {
    method: 'POST',
    body: { first_name: 'Wizard', last_name: 'Staff', email, role_type: 'TEACHER' },
  });
  await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${staffSessionId}/preview/`);
  const staffCommit = await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${staffSessionId}/commit/`, { method: 'POST' });
  const staffId = staffCommit?.result?.staff_id;
  if (!staffId) throw new Error(`Staff fixture missing staff_id: ${JSON.stringify(staffCommit)}`);
  const staffVerify = await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${staffSessionId}/verify/`);
  expect(staffVerify.staff_exists).toBeTruthy();

  const created = await authenticatedApiJson(page, '/api/v1/section-staffing-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { term: fixture.termCode || 'E2E' },
  });
  await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/load_sections/`, {
    method: 'POST', body: { sections_pool: [{ section_id: fixture.sectionId, section_name: 'E2E Section', course_code: 'E2E', grade_level: '7' }] },
  });
  await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/stage_assignments/`, {
    method: 'POST', body: { assignments: [{ section_id: fixture.sectionId, teacher_id: String(staffId), role: 'primary' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  expect(committed.assigned).toBe(1);
  const verified = await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/verify/`);
  expect(verified.status).toBe('verified');
});

test('Section Staffing denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-staffing-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-staffing-setup(?:$|\?)/i);
});
