import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createCanonicalSectionFixture, createStaffFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Section Staffing persists a canonical TeacherAssignment and verifies it', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/section-staffing-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/section-staffing-setup/);

  const section = await createCanonicalSectionFixture(page, 'Staffing');
  const teacher = await createStaffFixture(page, 'StaffingTeacher');
  const created = await authenticatedApiJson(page, '/api/v1/section-staffing-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { academic_year_id: section.academicYearId, term: section.termCode },
  });
  const loaded = await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/load_sections/`, {
    method: 'POST',
    body: { sections_pool: [{ section_id: section.sectionId, section_name: 'E2E Section', course_code: 'E2E', grade_level: '7' }] },
  });
  expect(loaded.section_count).toBe(1);
  await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/stage_assignments/`, {
    method: 'POST',
    body: { assignments: [{ section_id: section.sectionId, teacher_id: teacher.staffId, role: 'primary' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  const verified = await authenticatedApiJson(page, `/api/v1/section-staffing-wizard/sessions/${sessionId}/verify/`);
  expect(committed.assigned).toBe(1);
  expect(JSON.stringify(verified)).toContain(section.sectionId);
  expect(JSON.stringify(verified)).toContain(teacher.staffId);
});

test('Section Staffing denies an unauthorized Heritage Parent', async ({ page }) => {
  await launchHeritageRole(page, 'parent');
  await page.goto(`${frontendUrl}/section-staffing-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-staffing-setup(?:$|\?)/i);
});
