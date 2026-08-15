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
    const token = sessionStorage.getItem('crown.jwt.access') || localStorage.getItem('crown.jwt.access') || sessionStorage.getItem('crown_auth_token') || localStorage.getItem('crown_auth_token') || sessionStorage.getItem('access_token') || localStorage.getItem('access_token') || '';
    const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('schoolId') || localStorage.getItem('crown.school.id') || '';
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (schoolId) headers['X-School-Id'] = schoolId;
    const response = await fetch(requestPath, { method: requestInit.method || 'GET', headers, credentials: 'include', body: requestInit.body === undefined ? undefined : JSON.stringify(requestInit.body) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(`${requestInit.method || 'GET'} ${requestPath} -> ${response.status}: ${JSON.stringify(data)}`);
    return data;
  }, { requestPath: path, requestInit: init });
}

export async function authenticatedCsvUpload(page: Page, path: string, csv: string, filename = 'wizard-e2e.csv') {
  return page.evaluate(async ({ requestPath, csvText, fileName }) => {
    const token = sessionStorage.getItem('crown.jwt.access') || localStorage.getItem('crown.jwt.access') || sessionStorage.getItem('crown_auth_token') || localStorage.getItem('crown_auth_token') || sessionStorage.getItem('access_token') || localStorage.getItem('access_token') || '';
    const schoolId = sessionStorage.getItem('crown.school.id') || localStorage.getItem('schoolId') || localStorage.getItem('crown.school.id') || '';
    const headers: Record<string, string> = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (schoolId) headers['X-School-Id'] = schoolId;
    const form = new FormData();
    form.append('file', new File([csvText], fileName, { type: 'text/csv' }));
    const response = await fetch(requestPath, { method: 'POST', headers, credentials: 'include', body: form });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(`POST ${requestPath} -> ${response.status}: ${JSON.stringify(data)}`);
    return data;
  }, { requestPath: path, csvText: csv, fileName: filename });
}

export async function createAcademicYearFixture(page: Page, suffix: string) {
  const created = await authenticatedApiJson(page, '/api/v1/academic-year-wizard/sessions/', { method: 'POST' });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/configure/`, { method: 'POST', body: { year_name: `2032-2033-${suffix}`, start_date: '2032-08-15', end_date: '2033-06-15' } });
  await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/terms/`, { method: 'POST', body: { terms: [{ code: `FULL-${suffix}`, name: `Full Year ${suffix}`, school_year: `2032-33-${suffix}`, start_date: '2032-08-15', end_date: '2033-06-15', ordering: 0 }] } });
  const committed = await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/commit/`, { method: 'POST' });
  const verified = await authenticatedApiJson(page, `/api/v1/academic-year-wizard/sessions/${sessionId}/verify/`);
  const academicYearId = committed?.result?.academic_year_id || committed?.academic_year_id || verified?.academic_year_id || verified?.result?.academic_year_id;
  if (!academicYearId) throw new Error(`Academic year fixture did not return an id: ${JSON.stringify({ committed, verified })}`);
  return String(academicYearId);
}

export async function createCanonicalSectionFixture(page: Page, label: string) {
  const scope = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/scope-options/');
  const year = scope.academic_years?.find((item: any) => item.is_current) || scope.academic_years?.[0];
  const term = scope.terms?.find((item: any) => item.academic_year_id === year?.academic_year_id && item.active) || scope.terms?.find((item: any) => item.academic_year_id === year?.academic_year_id);
  if (!year?.academic_year_id || !term?.term_id) throw new Error(`No canonical scheduling scope: ${JSON.stringify(scope)}`);
  const created = await authenticatedApiJson(page, '/api/v1/scheduling-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/configure/`, { method: 'POST', body: { academic_year_id: year.academic_year_id, term_id: term.term_id } });
  const suffix = `${label}${Date.now().toString().slice(-5)}`.replace(/[^A-Za-z0-9]/g, '').slice(-10).toUpperCase();
  const courseCode = `E${suffix}`.slice(0, 12);
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/courses/`, { method: 'POST', body: { courses: [{ code: courseCode, name: `E2E ${label}`, department: 'Testing', credits: '1.0' }] } });
  const staged = await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/sections/`, { method: 'POST', body: { sections: [{ course_code: courseCode, teacher_name: 'E2E Teacher' }] } });
  const sectionId = staged.sections?.[0]?.section_id;
  if (!sectionId) throw new Error(`Scheduling fixture did not stage a section: ${JSON.stringify(staged)}`);
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/commit/`, { method: 'POST', body: { confirm: true } });
  await authenticatedApiJson(page, `/api/v1/scheduling-wizard/sessions/${sessionId}/verify/`);
  return { sectionId: String(sectionId), academicYearId: String(year.academic_year_id), termId: String(term.term_id), termCode: String(term.code || '') };
}

export async function createStaffFixture(page: Page, label: string) {
  const created = await authenticatedApiJson(page, '/api/v1/staff-onboarding-wizard/sessions/', { method: 'POST', body: {} });
  const sessionId = created.session_id;
  const suffix = Date.now().toString().slice(-8);
  const email = `e2e-${label.toLowerCase().replace(/[^a-z0-9]/g, '')}-${suffix}@school.test`;
  await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${sessionId}/configure/`, { method: 'POST', body: { first_name: 'E2E', last_name: label, email, role_type: 'TEACHER' } });
  await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${sessionId}/preview/`);
  const committed = await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${sessionId}/commit/`, { method: 'POST', body: { confirm: true } });
  const verified = await authenticatedApiJson(page, `/api/v1/staff-onboarding-wizard/sessions/${sessionId}/verify/`);
  const staffId = committed?.result?.staff_id;
  if (!staffId || !verified?.staff_exists) throw new Error(`Staff fixture failed: ${JSON.stringify({ committed, verified })}`);
  return { staffId: String(staffId), email };
}

export async function ensureHouseholdStudentFixture(page: Page) {
  await launchHeritageRole(page, 'parent');
  let state = await authenticatedApiJson(page, '/api/v1/sandbox/parent/enrollment/');
  if (!state.child_id) {
    state = await authenticatedApiJson(page, '/api/v1/sandbox/parent/enrollment/', { method: 'POST', body: { application_id: state.application_id, accepted_terms: true } });
  }
  if (!state.child_id) throw new Error(`Parent enrollment did not yield a household student: ${JSON.stringify(state)}`);
  return String(state.child_id);
}
