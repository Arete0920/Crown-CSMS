import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createSchedulingSectionFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Section Scheduler publishes and verifies a canonical section placement', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  const section = await createSchedulingSectionFixture(page, 'SCHED');

  const bell = await authenticatedApiJson(page, '/api/v1/bell-schedule-wizard/sessions/', { method: 'POST' });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bell.session_id}/configure/`, {
    method: 'POST',
    body: { schedule_name: `E2E Scheduler ${Date.now()}`, schedule_mode: 'SINGLE_DAY', academic_year_id: section.academicYearId },
  });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bell.session_id}/blocks/`, {
    method: 'POST',
    body: { templates: [{ template_code: 'DEFAULT', blocks: [{ code: 'P1', label: 'Period 1', start_time: '08:00', end_time: '08:50', is_instructional: true, is_lunch: false, is_break: false }] }] },
  });
  await authenticatedApiJson(page, `/api/v1/bell-schedule-wizard/sessions/${bell.session_id}/commit/`, { method: 'POST', body: {} });

  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /scheduling scope/i })).toBeVisible();
  await page.getByPlaceholder('Academic Year ID').fill(section.academicYearId);
  await page.getByPlaceholder(/term code/i).fill(section.termCode);

  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/section-scheduler-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  const optionsPromise = page.waitForResponse(r => r.url().includes('/options/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /load canonical sections/i }).click();
  expect((await createPromise).ok()).toBeTruthy();
  expect((await configurePromise).ok()).toBeTruthy();
  const optionsResponse = await optionsPromise;
  expect(optionsResponse.ok()).toBeTruthy();
  const options = await optionsResponse.json();
  expect(options.sections?.some((item: { section_id: string }) => item.section_id === section.sectionId)).toBeTruthy();
  expect(options.day_templates?.length).toBeGreaterThan(0);
  expect(options.day_templates[0]?.blocks?.length).toBeGreaterThan(0);

  await expect(page.getByRole('heading', { name: /section placements/i })).toBeVisible();
  const selects = page.locator('select');
  await selects.nth(0).selectOption(section.sectionId);
  await selects.nth(1).selectOption(options.day_templates[0].day_template_id);
  await selects.nth(2).selectOption(options.day_templates[0].blocks[0].period_block_id);

  const sectionsPromise = page.waitForResponse(r => r.url().includes('/sections/') && r.request().method() === 'POST');
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /publish placements/i }).click();
  const [sectionsResponse, commitResponse, verifyResponse] = await Promise.all([sectionsPromise, commitPromise, verifyPromise]);
  expect(sectionsResponse.ok()).toBeTruthy();
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();
  const verified = await verifyResponse.json();
  expect(verified.count).toBeGreaterThanOrEqual(1);

  await expect(page.getByRole('heading', { name: /scheduling verified/i })).toBeVisible();
  await expect(page.getByText(/verified placements:/i)).not.toContainText('undefined');
});

test('Section Scheduler denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-scheduler-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-scheduler-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /scheduling scope/i })).toHaveCount(0);
});
