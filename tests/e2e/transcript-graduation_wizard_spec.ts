import { test, expect, type Page, type Route } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

const studentId = '11111111-1111-4111-8111-111111111111';
const issuanceId = '22222222-2222-4222-8222-222222222222';
const artifactSha = 'a'.repeat(64);
const json = (route: Route, body: unknown, status = 200) =>
  route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });

const transcript = {
  student: { student_id: studentId, first_name: 'Jordan', last_name: 'Heritage', grade_level: '12' },
  terms: [{
    term_id: '33333333-3333-4333-8333-333333333333', term_code: 'FALL', term_name: 'Fall 2026',
    term_gpa: '4.00', attempted_credits: '1.00', earned_credits: '1.00',
    courses: [{
      section_id: '44444444-4444-4444-8444-444444444444', course_code: 'ENG-401',
      course_name: 'Senior English', teacher_name: 'A. Teacher', final_percent: 96,
      final_letter: 'A', credits: '1.00', earned_credits: '1.00', record_status: 'final',
      provider: 'Heritage Christian School', dual_enrollment_label: '',
    }],
  }],
  cumulative_gpa: '4.00', attempted_credits: '1.00', earned_credits: '1.00', notes: [],
};

async function mockTranscriptApis(page: Page) {
  await page.route('**/api/v1/students/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/students/' || path === '/api/v1/students') {
      return json(route, { results: [{ id: studentId, first_name: 'Jordan', last_name: 'Heritage', grade_level: '12' }] });
    }
    return route.continue();
  });
  await page.route(`**/api/v1/academics/transcript/${studentId}/`, (route) => json(route, transcript));
  await page.route(`**/api/v1/academics/students/${studentId}/transcript/issuances/`, (route) => {
    expect(route.request().method()).toBe('POST');
    return json(route, { issuance_id: issuanceId, artifact_sha256: artifactSha }, 201);
  });
  await page.route(`**/api/v1/academics/transcript-issuances/${issuanceId}/pdf/`, (route) =>
    route.fulfill({ status: 200, contentType: 'application/pdf', body: '%PDF-1.4\n% transcript proof\n' }));
}

async function openTranscript(page: Page, role: string) {
  await mockTranscriptApis(page);
  await launchHeritageRole(page, role);
  await page.goto(`${frontendUrl}/transcript`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: 'Academic Transcript' })).toBeVisible();
}

test('academic staff sees authoritative transcript and can issue official PDF', async ({ page }) => {
  await openTranscript(page, 'head_of_school');
  await expect(page.getByText('Senior English')).toBeVisible();
  await expect(page.getByText('Term GPA: 4.00')).toBeVisible();
  await expect(page.getByText(/MVP/i)).toHaveCount(0);
  const issue = page.getByRole('button', { name: 'Issue Official PDF' });
  await expect(issue).toBeVisible();
  await issue.click();
  await expect(page.getByRole('status')).toContainText(issuanceId);
  await expect(page.getByRole('status')).toContainText(artifactSha);
});

test('family transcript reader cannot issue official PDF', async ({ page }) => {
  await openTranscript(page, 'parent');
  await expect(page.getByRole('button', { name: 'Issue Official PDF' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Print Working Copy' })).toBeVisible();
});
