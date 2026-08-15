import { expect, type Page } from '@playwright/test';

export const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';

export async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  const roleSelect = page.locator('#login-role').first();
  await expect(roleSelect).toBeVisible();
  const sandboxRole = role === 'admin' || role === 'head_of_school' ? 'school_admin' : role;
  await roleSelect.selectOption(sandboxRole);
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
    const csrfToken = document.cookie
      .split(';')
      .map((part) => part.trim())
      .find((part) => part.startsWith('csrftoken='))
      ?.slice('csrftoken='.length) || '';
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (schoolId) headers['X-School-Id'] = schoolId;
    if (csrfToken && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes((requestInit.method || 'GET').toUpperCase())) {
      headers['X-CSRFToken'] = decodeURIComponent(csrfToken);
    }
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

export function resultList(data: any): any[] {
  if (Array.isArray(data)) return data;
  for (const key of ['results', 'items', 'sections', 'students', 'staff', 'rooms']) {
    if (Array.isArray(data?.[key])) return data[key];
  }
  return [];
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

export async function createSchedulingFixture(page: Page, suffix: string) {
  const academicYearId = await createAcademicYearFixture(page, suffix);
  const scope = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/scope-options/');
  const terms = Array.isArray(scope?.terms) ? scope.terms : [];
  const term = terms.find((item: any) => String(item.academic_year_id) === academicYearId) || terms.at(-1);
  if (!term?.term_id) throw new Error(`Scheduling fixture could not resolve term: ${JSON.stringify(scope)}`);

  const created = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`, {
    method: 'POST',
    body: { academic_year_id: academicYearId, term_id: String(term.term_id) },
  });
  const code = `E2E${suffix}`.replace(/[^A-Z0-9]/gi, '').slice(0, 20).toUpperCase();
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`, {
    method: 'POST',
    body: { courses: [{ code, name: `E2E ${suffix} Course`, department: 'CERT', credits: 1 }] },
  });
  const staged = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`, {
    method: 'POST',
    body: { sections: [{ course_code: code, teacher_name: 'E2E Teacher', grade_band: '7' }] },
  });
  const committed = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`, {
    method: 'POST',
    body: { confirm: true },
  });
  const verified = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`);
  const sectionId = committed?.section_ids?.[0] || staged?.sections?.[0]?.section_id || verified?.section_ids?.[0];
  if (!sectionId) throw new Error(`Scheduling fixture did not return section id: ${JSON.stringify({ staged, committed, verified })}`);
  return { academicYearId, termId: String(term.term_id), termCode: String(term.code || term.term_code || ''), sectionId: String(sectionId), sessionId };
}
