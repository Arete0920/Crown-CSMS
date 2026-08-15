import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createSchedulingFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Gradebook Setup persists weighted categories against a canonical section and verifies them', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/gradebook-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/gradebook-setup/);

  const fixture = await createSchedulingFixture(page, `GRADE${Date.now().toString().slice(-6)}`);
  const created = await authenticatedApiJson(page, '/api/v1/gradebook-setup-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { section_id: fixture.sectionId },
  });
  await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/categories/`, {
    method: 'POST',
    body: { categories: [
      { name: 'Homework', weight_percent: 30, sort_order: 1 },
      { name: 'Quizzes', weight_percent: 30, sort_order: 2 },
      { name: 'Tests', weight_percent: 40, sort_order: 3 },
    ] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  expect(committed.status).toBe('committed');
  expect(committed.total).toBe(3);

  const verified = await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/verify/`);
  expect(verified.status).toBe('verified');
  expect(verified.category_count).toBe(3);
  expect(String(verified.section_id)).toBe(fixture.sectionId);
});

test('Gradebook Setup denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/gradebook-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/gradebook-setup(?:$|\?)/i);
});
