import { expect, test, type Page } from '@playwright/test';

const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';
const demoSchoolId = process.env.CROWN_DEMO_SCHOOL_ID || '19801b59-8c05-4c84-9312-5d792e4e839d';

async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  await page.locator('#login-role').first().selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

async function currentAcademicYear(page: Page) {
  const response = await page.context().request.get(`${frontendUrl}/api/v1/academics/years/`, {
    headers: { 'X-School-Id': demoSchoolId },
  });
  expect(response.ok(), `academic years returned ${response.status()}`).toBeTruthy();
  const body = await response.json();
  const rows = body.results || body;
  const current = rows.find((row: any) => row.is_current) || rows[0];
  expect(current?.year_id).toBeTruthy();
  return current;
}

test('Term Structure wizard persists full-year periods and commits live structure', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  const year = await currentAcademicYear(page);
  await page.goto(`${frontendUrl}/term-structure-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /configure structure/i })).toBeVisible();

  await page.getByPlaceholder(/uuid of the academic year/i).fill(year.year_id);
  await page.locator('select').first().selectOption('SEMESTER');
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/term-structure-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next: set periods/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /marking periods/i })).toBeVisible();
  const rows = page.locator('tbody tr');
  await rows.nth(0).locator('input[type="text"]').nth(0).fill('S1-E2E');
  await rows.nth(0).locator('input[type="text"]').nth(1).fill('Semester 1 E2E');
  await rows.nth(0).locator('input[type="date"]').nth(0).fill(year.start_date);
  const midpoint = `${year.start_date.slice(0, 4)}-12-31`;
  await rows.nth(0).locator('input[type="date"]').nth(1).fill(midpoint);
  await rows.nth(1).locator('input[type="text"]').nth(0).fill('S2-E2E');
  await rows.nth(1).locator('input[type="text"]').nth(1).fill('Semester 2 E2E');
  const nextDay = `${Number(year.start_date.slice(0, 4)) + 1}-01-01`;
  await rows.nth(1).locator('input[type="date"]').nth(0).fill(nextDay);
  await rows.nth(1).locator('input[type="date"]').nth(1).fill(year.end_date);

  const periodsPromise = page.waitForResponse(r => r.url().includes('/periods/') && r.request().method() === 'POST');
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /commit structure/i }).click();
  const [periodsResponse, commitResponse] = await Promise.all([periodsPromise, commitPromise]);
  expect(periodsResponse.ok()).toBeTruthy();
  expect(commitResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /term structure committed/i })).toBeVisible();
  await expect(page.getByText(/structure type/i)).toBeVisible();
  await expect(page.getByText(/term structure id/i)).not.toContainText('undefined');
});

test('Term Structure wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/term-structure-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/term-structure-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /configure structure/i })).toHaveCount(0);
});