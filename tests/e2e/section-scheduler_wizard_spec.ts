import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createAcademicYearFixture, createCanonicalSectionFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Section Scheduler publishes and verifies a canonical placement', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /Scheduling Scope/i })).toBeVisible();

  const suffix = `SS${Date.now().toString().slice(-5)}`;
  const academicYearId = await createAcademicYearFixture(page, suffix);
  const termCode = `FULL-${suffix}`;

  const tsCreated = await authenticatedApiJson(page, '/api/v1/term-structure-wizard/sessions/', { method: 'POST', body: {} });
  const tsId = tsCreated.session_id;
  await authenticatedApiJson(page, `/api/v1/term-structure-wizard/sessions/${tsId}/configure/`, {
    method: 'POST', body: { academic_year_id: academicYearId, structure_type: 'SEMESTER' },
  });
  await authenticatedApiJson(page, `/api/v1/term-structure-wizard/sessions/${tsId}/periods/`, {
    method: 'POST', body: [{ code: termCode, name: 'Full Year', start_date: '2032-08-15', end_date: '2033-06-15', is_grade_term: true }],
  });
  await authenticatedApiJson(page, `/api/v1/term-structure-wizard/sessions/${tsId}/commit/`, { method: 'POST', body: { confirm: true } });
  await authenticatedApiJson(page, `/api/v1/term-structure-wizard/sessions/${tsId}/verify/`);

  const bellCreated = await authenticatedApiJson(page, '/api/v1/bell-schedule-wizard/sessions/', { method: 'POST', body: {} });
  const bellId = bellCreated.session_id;
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bellId}/configure/`, {
    method: 'POST', body: { schedule_name: `E2E Scheduler ${suffix}`, schedule_mode: 'SINGLE_DAY', academic_year_id: academicYearId },
  });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bellId}/blocks/`, {
    method: 'POST',
    body: { templates: [{ template_code: 'DEFAULT', blocks: [{ code: 'P1', label: 'Period 1', start_time: '08:00', end_time: '08:50', is_instructional: true }] }] },
  });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bellId}/commit/`, { method: 'POST', body: { confirm: true } });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bellId}/verify/`);

  const canonicalSection = await createCanonicalSectionFixture(page, 'Scheduler');
  expect(canonicalSection.academicYearId).toBe(academicYearId);
  expect(canonicalSection.termCode).toBe(termCode);

  const created = await authenticatedApiJson(page, '/api/v1/section-scheduler-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { academic_year_id: academicYearId, term_code: termCode },
  });
  const options = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/options/`);
  const section = options.sections?.find((item: any) => item.section_id === canonicalSection.sectionId) || options.sections?.[0];
  const template = options.day_templates?.find((item: any) => item.blocks?.length) || options.day_templates?.[0];
  const block = template?.blocks?.[0];
  expect(section?.section_id).toBeTruthy();
  expect(template?.day_template_id).toBeTruthy();
  expect(block?.period_block_id).toBeTruthy();

  await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/sections/`, {
    method: 'POST',
    body: { sections: [{ section_id: section.section_id, day_template_id: template.day_template_id, period_block_id: block.period_block_id, room_id: options.rooms?.[0]?.room_id || '' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  const verified = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/verify/`);
  expect(committed.total).toBe(1);
  expect(verified.count).toBe(1);
  expect(verified.sections?.[0]?.section_id).toBe(section.section_id);
});

test('Section Scheduler denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-scheduler-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /Scheduling Scope/i })).toHaveCount(0);
});
