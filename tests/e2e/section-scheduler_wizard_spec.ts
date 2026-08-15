import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createSchedulingFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Section Scheduler publishes a real canonical placement and verifies persistence', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /section scheduler/i })).toBeVisible();

  const fixture = await createSchedulingFixture(page, `PLACE${Date.now().toString().slice(-6)}`);
  const created = await authenticatedApiJson(page, '/api/v1/section-scheduler-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: { academic_year_id: fixture.academicYearId, term_code: fixture.termCode },
  });
  const options = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/options/`);
  const section = (options.sections || []).find((row: any) => String(row.section_id) === fixture.sectionId) || options.sections?.[0];
  const dayTemplate = options.day_templates?.[0];
  const block = dayTemplate?.blocks?.[0];
  if (!section || !dayTemplate || !block) throw new Error(`Heritage scheduler options incomplete: ${JSON.stringify(options)}`);

  await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/sections/`, {
    method: 'POST',
    body: {
      sections: [{
        section_id: String(section.section_id),
        day_template_id: String(dayTemplate.day_template_id),
        period_block_id: String(block.period_block_id),
        room_id: options.rooms?.[0]?.room_id ? String(options.rooms[0].room_id) : '',
      }],
    },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST',
    body: { confirm: true },
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
