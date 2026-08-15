import { expect, test } from '@playwright/test';
import { authenticatedApiJson, createCanonicalSectionFixture, ensureHouseholdStudentFixture, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Section Assign persists a real roster enrollment and verifies it', async ({ page }) => {
  const studentId = await ensureHouseholdStudentFixture(page);
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/section-assign-setup`, { waitUntil: 'networkidle' });
  await expect(page).toHaveURL(/\/section-assign-setup/);

  const section = await createCanonicalSectionFixture(page, 'Roster');
  const created = await authenticatedApiJson(page, '/api/v1/section-assign-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST', body: { section_id: section.sectionId, term: section.termCode },
  });
  const loaded = await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/load/`, {
    method: 'POST', body: { student_ids: [studentId] },
  });
  expect(loaded).toBeTruthy();
  await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/stage/`, {
    method: 'POST', body: { changes: [{ student_id: studentId, action: 'add' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  const verified = await authenticatedApiJson(page, `/api/v1/section-assign-wizard/sessions/${sessionId}/verify/`);
  expect(committed).toBeTruthy();
  expect(JSON.stringify(verified)).toContain(studentId);
  expect(JSON.stringify(verified)).toContain(section.sectionId);
});

test('Section Assign denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/section-assign-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/section-assign-setup(?:$|\?)/i);
});
