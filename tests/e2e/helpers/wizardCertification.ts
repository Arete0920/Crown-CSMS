import { expect, type Page } from '@playwright/test';

export const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';

export async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  const roleSelect = page.locator('#login-role').first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

export async function authenticatedApiJson(
  page: Page,
  path: string,
  init: { method?: string; body?: unknown } = {},
) {
  return page.evaluate(async ({ requestPath, requestInit }) => {
    const token =
      sessionStorage.getItem('crown.jwt.access') ||
      localStorage.getItem('crown.jwt.access') ||
      sessionStorage.getItem('crown_auth_token') ||
      localStorage.getItem('crown_auth_token') ||
      sessionStorage.getItem('access_token') ||
      localStorage.getItem('access_token') ||
      '';
    const schoolId =
      sessionStorage.getItem('crown.school.id') ||
      localStorage.getItem('schoolId') ||
      localStorage.getItem('crown.school.id') ||
      '';
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (schoolId) headers['X-School-Id'] = schoolId;
    const response = await fetch(requestPath, {
      method: requestInit.method || 'GET',
      headers,
      credentials: 'include',
      body: requestInit.body === undefined ? undefined : JSON.stringify(requestInit.body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(`${requestInit.method || 'GET'} ${requestPath} -> ${response.status}: ${JSON.stringify(data)}`);
    }
    return data;
  }, { requestPath: path, requestInit: init });
}

export async function createAcademicYearFixture(page: Page, suffix: string) {
  const created = await authenticatedApiJson(page, '/api/v1/academic-year-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: {
      year_name: `2032-2033-${suffix}`,
      start_date: '2032-08-15',
      end_date: '2033-06-15',
    },
  });
  await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/terms/`, {
    method: 'POST',
    body: {
      terms: [
        {
          code: `FULL-${suffix}`,
          name: `Full Year ${suffix}`,
          school_year: `2032-33-${suffix}`,
          start_date: '2032-08-15',
          end_date: '2033-06-15',
          ordering: 0,
        },
      ],
    },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/commit/`, { method: 'POST' });
  const verified = await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/verify/`);
  const academicYearId = committed?.result?.academic_year_id || committed?.academic_year_id || verified?.academic_year_id || verified?.result?.academic_year_id;
  if (!academicYearId) throw new Error(`Academic year fixture did not return an id: ${JSON.stringify({ committed, verified })}`);
  return String(academicYearId);
}

export async function getCanonicalStudentFixture(page: Page) {
  const payload = await authenticatedApiJson(page, '/api/v1/students/?limit=100&offset=0');
  const students = Array.isArray(payload) ? payload : payload.students || payload.results || payload.data || [];
  const student = students.find((item: { id?: string; student_id?: string; is_active?: boolean }) => item?.is_active !== false && (item?.id || item?.student_id))
    || students.find((item: { id?: string; student_id?: string }) => item?.id || item?.student_id);
  const studentId = student?.id || student?.student_id;
  if (!studentId) throw new Error(`Canonical student fixture unavailable: ${JSON.stringify(payload)}`);
  return { ...student, studentId: String(studentId) };
}

export async function createSchedulingSectionFixture(page: Page, suffix: string) {
  const scope = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/scope-options/');
  const academicYear = scope.academic_years?.find((year: { is_current?: boolean }) => year.is_current) || scope.academic_years?.[0];
  const term = scope.terms?.find((item: { academic_year_id: string; active?: boolean }) => item.academic_year_id === academicYear?.academic_year_id && item.active)
    || scope.terms?.find((item: { academic_year_id: string }) => item.academic_year_id === academicYear?.academic_year_id);
  if (!academicYear?.academic_year_id || !term?.term_id) {
    throw new Error(`Scheduling scope missing academic year/term: ${JSON.stringify(scope)}`);
  }

  const created = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: { academic_year_id: academicYear.academic_year_id, term_id: term.term_id },
  });
  const courseCode = `FX${suffix}${Date.now().toString().slice(-6)}`.toUpperCase();
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`, {
    method: 'POST',
    body: { courses: [{ code: courseCode, name: `Fixture ${suffix}`, department: 'E2E', credits: '1.0' }] },
  });
  const staged = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`, {
    method: 'POST',
    body: { sections: [{ course_code: courseCode, teacher_name: 'Fixture Teacher', grade_band: '7' }] },
  });
  const sectionId = staged.sections?.[0]?.section_id;
  if (!sectionId) throw new Error(`Scheduling fixture did not stage a section: ${JSON.stringify(staged)}`);
  const committed = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST',
    body: { confirm: true },
  });
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`);
  return {
    sectionId: String(sectionId),
    academicYearId: String(academicYear.academic_year_id),
    termId: String(term.term_id),
    termCode: String(term.code),
    courseCode,
    commit: committed,
  };
}
