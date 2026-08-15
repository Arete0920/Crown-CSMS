import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createCanonicalSectionFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Gradebook Setup persists weighted categories for a canonical section and verifies them', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/gradebook-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByText(/Gradebook Setup/i)).toBeVisible();

  const { sectionId } = await createCanonicalSectionFixture(page, 'Gradebook');
  const created = await authenticatedApiJson(page, '/api/v1/gradebook-setup-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { section_id: sectionId },
  });
  const categories = [
    { name: 'Homework E2E', weight_percent: 30, sort_order: 0 },
    { name: 'Quizzes E2E', weight_percent: 30, sort_order: 1 },
    { name: 'Tests E2E', weight_percent: 40, sort_order: 2 },
  ];
  const defined = await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/categories/`, {
    method: 'POST', body: { categories },
  });
  expect(defined.total_weight).toBe(100);

  const committed = await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  const verified = await authenticatedApiJson(page, `/api/v1/gradebook-setup-wizard/sessions/${sessionId}/verify/`);
  expect(committed).toBeTruthy();
  expect(JSON.stringify(verified)).toContain('Homework E2E');
  expect(JSON.stringify(verified)).toContain(sectionId);
});

test('Gradebook Setup denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/gradebook-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/gradebook-setup(?:$|\?)/i);
  await expect(page.getByText(/Gradebook Setup/i)).toHaveCount(0);
});
