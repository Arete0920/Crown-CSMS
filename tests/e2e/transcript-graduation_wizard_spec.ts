import { test, expect } from '@playwright/test';
import { frontendUrl, launchHeritageRole } from './helpers/wizardCertification';

const studentId = '11111111-1111-4111-8111-111111111111';
const issuanceId = '22222222-2222-4222-8222-222222222222';
const artifactSha = 'a'.repeat(64);

const transcriptPayload = {
  student: {
    student_id: studentId,
    first_name: 'Jordan',
    last_name: 'Heritage',
    grade_level: '12',
  },
  terms: [
    {
      term_id: '33333333-3333-4333-8333-333333333333',
      term_code: 'FALL',
      term_name: 'Fall 2026',
      school_year: '2026-2027',
      term_gpa: '4.00',
      attempted_credits: '1.00',
      earned_credits: '1.00',
      courses: [
        {
          section_id: '44444444-4444-4444-8444-444444444444',
          course_code: 'ENG-401',
          course_name: 'Senior English',
          teacher_name: 'A. Teacher',
          final_percent: 96.0,
          final_letter: 'A',
          credits: '1.00',
          attempted_credits: '1.00',
          earned_credits: '1.00',
          gpa_points: '4.00',
          gpa_included: true,
          record_status: 'final',
          provider: 'Heritage Christian School',
          dual_enrollment_label: '',
        },
      ],
    },
  ],
  cumulative_gpa: '4.00',
  attempted_credits: '1.00',
  earned_credits: '1.00',
  notes: ['GPA and earned-credit totals include finalized transcript entries only.'],
};

async function mockTranscriptApis(page) {
  await page.route('**/api/v1/students/**', async (route) => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/v1/students/' || url.pathname === '/api/v1/students') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: studentId,
              first_name: 'Jordan',
              middle_name: '',
              last_name: 'Heritage',
              grade_level: '12',
            },
          ],
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.route(`**/api/v1/academics/transcript/${studentId}/`, async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(transcriptPayload) });
  });

  await page.route(`**/api/v1/academics/students/${studentId}/transcript/issuances/`, async (route) => {
    expect(route.request().method()).toBe('POST');
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        issuance_id: issuanceId,
        student_id: studentId,
        issued_at: '2026-08-16T00:00:00Z',
        source_sha256: 'b'.repeat(64),
        artifact_sha256: artifactSha,
        download_url: `/api/v1/academics/transcript-issuances/${issuanceId}/pdf/`,
      }),
    });
  });

  await page.route(`**/api/v1/academics/transcript-issuances/${issuanceId}/pdf/`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      headers: {
        'Content-Disposition': 'attachment; filename="official-transcript.pdf"',
        'X-CROWN-Transcript-Issuance': issuanceId,
        'X-CROWN-Artifact-SHA256': artifactSha,
      },
      body: '%PDF-1.4\n% CROWN transcript proof\n',
    });
  });
}

test('academic staff sees authoritative transcript and can issue official PDF', async ({ page }) => {
  await mockTranscriptApis(page);
  await launchHeritageRole(page, 'head_of_school');
  await page.goto(`${frontendUrl}/transcript`, { waitUntil: 'networkidle' });

  await expect(page.getByRole('heading', { name: 'Academic Transcript' })).toBeVisible();
  await expect(page.getByText('Senior English')).toBeVisible();
  await expect(page.getByText('Term GPA: 4.00')).toBeVisible();
  await expect(page.getByText('Cumulative GPA')).toBeVisible();
  await expect(page.getByText(/MVP/i)).toHaveCount(0);

  const issueButton = page.getByRole('button', { name: 'Issue Official PDF' });
  await expect(issueButton).toBeVisible();
  await issueButton.click();

  await expect(page.getByRole('status')).toContainText(issuanceId);
  await expect(page.getByRole('status')).toContainText(artifactSha);
});

test('family transcript reader does not see official issuance control', async ({ page }) => {
  await mockTranscriptApis(page);
  await launchHeritageRole(page, 'parent');
  await page.goto(`${frontendUrl}/transcript`, { waitUntil: 'networkidle' });

  await expect(page.getByRole('heading', { name: 'Academic Transcript' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Issue Official PDF' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Print Working Copy' })).toBeVisible();
});
