import { expect, test } from '@playwright/test';
import { authenticatedApiJson, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Section Scheduler publishes and verifies a canonical placement', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /Scheduling Scope/i })).toBeVisible();

  const scope = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/scope-options/');
  const year = scope.academic_years?.find((item: any) => item.is_current) || scope.academic_years?.[0];
  const term = scope.terms?.find((item: any) => item.academic_year_id === year?.academic_year_id && item.active)
    || scope.terms?.find((item: any) => item.academic_year_id === year?.academic_year_id);
  expect(year?.academic_year_id).toBeTruthy();
  expect(term?.code).toBeTruthy();

  const created = await authenticatedApiJson(page, '/api/v1/section-scheduler-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { academic_year_id: year.academic_year_id, term_code: term.code },
  });
  const options = await authenticatedApiJson(page, `/api/v1/section-scheduler-wizard/sessions/${sessionId}/options/`);
  const section = options.sections?.[0];
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
  expect((committed.total ?? committed.created ?? committed.updated)).toBeDefined();
  expect(verified.count).toBeGreaterThan(0);
});

test('Section Scheduler denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-scheduler-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /Scheduling Scope/i })).toHaveCount(0);
});
