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
      name: `2032-2033-${suffix}`,
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
