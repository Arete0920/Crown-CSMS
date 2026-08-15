import { expect, test } from '@playwright/test';
import {
  authenticatedApiJson,
  createCanonicalStaffFixture,
  createSchedulingSectionFixture,
  frontendUrl,
  launchHeritageRole,
} from './helpers/wizardCertification';

test('Section Staffing writes and verifies a canonical TeacherAssignment', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const suffix = Math.random().toString(16).slice(2, 8).toUpperCase();
  const section = await createSchedulingSectionFixture(page, `STAFF${suffix}`);
  const staff = await createCanonicalStaffFixture(page, `STAFF${suffix}`);
  const base = '/api/v1/section-staffing-wizard/sessions/';

  const created = await authenticatedApiJson(page, base, { method: 'POST' });
  expect(created.session_id).toBeTruthy();
  const sessionId = created.session_id;

  const configured = await authenticatedApiJson(page, `${base}${sessionId}/configure/`, {
    method: 'POST',
    body: { academic_year_id: section.academicYearId, term: section.termCode },
  });
  expect(configured.status).toBe('configured');
  expect(configured.academic_year_id).toBe(section.academicYearId);

  const loaded = await authenticatedApiJson(page, `${base}${sessionId}/load_sections/`, {
    method: 'POST',
    body: { sections_pool: [{ section_id: section.sectionId, course_code: section.courseCode }] },
  });
  expect(loaded.status).toBe('sections_loaded');
  expect(loaded.section_count).toBe(1);

  const staged = await authenticatedApiJson(page, `${base}${sessionId}/stage_assignments/`, {
    method: 'POST',
    body: { assignments: [{ section_id: section.sectionId, teacher_id: staff.staffId, role: 'primary' }] },
  });
  expect(staged.status).toBe('assignments_staged');
  expect(staged.assignment_count).toBe(1);

  const committed = await authenticatedApiJson(page, `${base}${sessionId}/commit/`, {
    method: 'POST',
    body: { confirm: true },
  });
  expect(committed.status).toBe('committed');
  expect(committed.requested).toBe(1);
  expect(committed.errors).toEqual([]);

  const verified = await authenticatedApiJson(page, `${base}${sessionId}/verify/`);
  expect(verified.status).toBe('verified');
  expect(verified.requested).toBe(1);
  expect(verified.errors).toEqual([]);

  await page.goto(`${frontendUrl}/section-staffing-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByText(/section staffing/i).first()).toBeVisible();
});

test('Section Staffing denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-staffing-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-staffing-setup(?:$|\?)/i);
  await expect(page.getByText(/section staffing/i)).toHaveCount(0);
});
