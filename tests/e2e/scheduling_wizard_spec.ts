import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createSchedulingFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Scheduling creates canonical course/section persistence and verifies the live session', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/scheduling-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/scheduling-setup/);

  const fixture = await createSchedulingFixture(page, `SCHED${Date.now().toString().slice(-6)}`);
  const verified = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${fixture.sessionId}/verify/`);
  expect(verified.status).toBe('verified');
  expect(verified.section_ids).toContain(fixture.sectionId);

  const sections = await authenticatedApiJson(page, '/api/v1/academics/sections/?limit=200');
  const rows = Array.isArray(sections?.results) ? sections.results : [];
  expect(rows.some((row: any) => String(row.id) === fixture.sectionId)).toBeTruthy();
});

test('Scheduling denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/scheduling-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/scheduling-setup(?:$|\?)/i);
});
