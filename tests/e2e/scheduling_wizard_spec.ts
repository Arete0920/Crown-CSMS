import { expect, test } from '@playwright/test';
import { authenticatedApiJson, frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

test('Scheduling wizard commits canonical course and section data and verifies persisted state', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/scheduling-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByText('Scheduling Setup')).toBeVisible();
  await expect(page.getByText(/Scheduling Scope/i)).toBeVisible();

  const scope = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/scope-options/');
  const year = scope.academic_years?.find((item: any) => item.is_current) || scope.academic_years?.[0];
  const term = scope.terms?.find((item: any) => item.academic_year_id === year?.academic_year_id && item.active)
    || scope.terms?.find((item: any) => item.academic_year_id === year?.academic_year_id);
  expect(year?.academic_year_id).toBeTruthy();
  expect(term?.term_id).toBeTruthy();

  const created = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: { academic_year_id: year.academic_year_id, term_id: term.term_id },
  });

  const suffix = Date.now().toString().slice(-6);
  const courseCode = `E2E${suffix}`;
  const courses = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`, {
    method: 'POST',
    body: { courses: [{ code: courseCode, name: `E2E Course ${suffix}`, department: 'Testing', credits: '1.0' }] },
  });
  expect(courses).toBeTruthy();

  const staged = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`, {
    method: 'POST',
    body: { sections: [{ course_code: courseCode, teacher_name: 'E2E Teacher' }] },
  });
  expect(staged.sections?.[0]?.section_id).toBeTruthy();

  const committed = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST', body: { confirm: true },
  });
  const verified = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`);
  expect(committed).toBeTruthy();
  expect(verified).toBeTruthy();
  expect(JSON.stringify(verified)).toContain(courseCode);
});

test('Scheduling wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/scheduling-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/scheduling-setup(?:$|\?)/i);
  await expect(page.getByText(/Scheduling Scope/i)).toHaveCount(0);
});
