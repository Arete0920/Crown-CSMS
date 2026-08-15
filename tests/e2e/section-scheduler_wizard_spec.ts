import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createSchedulingFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

async function createSectionSchedulerPrerequisites(page: any, fixture: any) {
  const termSession = await authenticatedApiJson(page, '/api/v1/term-structure-wizard/sessions/', { method: 'POST' });
  await authenticatedApiJson(page, `/api/v1/term-structure-wizard/sessions/${termSession.session_id}/configure/`, {
    method: 'POST', body: { academic_year_id: fixture.academicYearId, structure_type: 'CUSTOM' },
  });
  await authenticatedApiJson(page, `/api/v1/term-structure-wizard/sessions/${termSession.session_id}/periods/`, {
    method: 'POST',
    body: [{
      code: fixture.termCode,
      name: `Scheduler ${fixture.termCode}`,
      start_date: '2032-08-15',
      end_date: '2033-06-15',
      is_grade_term: true,
    }],
  });
  await authenticatedApiJson(page, `/api/v1/term-structure-wizard/sessions/${termSession.session_id}/commit/`, { method: 'POST' });

  const bellSession = await authenticatedApiJson(page, '/api/v1/bell-schedule-wizard/sessions/', { method: 'POST' });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bellSession.session_id}/configure/`, {
    method: 'POST',
    body: { schedule_name: `Scheduler ${fixture.termCode}`, schedule_mode: 'SINGLE_DAY', academic_year_id: fixture.academicYearId },
  });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bellSession.session_id}/blocks/`, {
    method: 'POST',
    body: { templates: [{
      template_code: 'DEFAULT',
      blocks: [{ code: 'P1', label: 'Period 1', start_time: '08:00', end_time: '08:50', is_instructional: true }],
    }] },
  });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bellSession.session_id}/commit/`, { method: 'POST' });
}

test('Section Scheduler publishes a real canonical placement and verifies persistence', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /section scheduler/i })).toBeVisible();

  const fixture = await createSchedulingFixture(page, `PLACE${Date.now().toString().slice(-6)}`);
  await createSectionSchedulerPrerequisites(page, fixture);

  const created = await authenticatedApiJson(page, '/api/v1/section-scheduler-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { academic_year_id: fixture.academicYearId, term_code: fixture.termCode },
  });
  const options = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/options/`);
  const section = (options.sections || []).find((row: any) => String(row.section_id) === fixture.sectionId) || options.sections?.[0];
  const dayTemplate = options.day_templates?.[0];
  const block = dayTemplate?.blocks?.[0];
  if (!section || !dayTemplate || !block) throw new Error(`Heritage scheduler options incomplete: ${JSON.stringify(options)}`);

  await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/sections/`, {
    method: 'POST',
    body: { sections: [{
      section_id: String(section.section_id),
      day_template_id: String(dayTemplate.day_template_id),
      period_block_id: String(block.period_block_id),
      room_id: options.rooms?.[0]?.room_id ? String(options.rooms[0].room_id) : '',
    }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  expect(committed.status).toBe('committed');

  const verified = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/verify/`);
  expect(verified.status).toBe('verified');
  expect(verified.count).toBeGreaterThanOrEqual(1);
});

test('Section Scheduler denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-scheduler-setup(?:$|\?)/i);
});
