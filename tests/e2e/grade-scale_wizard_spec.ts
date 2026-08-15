import { expect, test, type Page } from '@playwright/test';

const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';
const demoSchoolId = process.env.CROWN_DEMO_SCHOOL_ID || '19801b59-8c05-4c84-9312-5d792e4e839d';

async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  await page.locator('#login-role').first().selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

async function currentAcademicYearId(page: Page): Promise<string> {
  const response = await page.context().request.get(`${frontendUrl}/api/v1/academics/years/`, {
    headers: { 'X-School-Id': demoSchoolId },
  });
  expect(response.ok(), `academic years returned ${response.status()}`).toBeTruthy();
  const body = await response.json();
  const rows = body.results || body;
  const current = rows.find((row: any) => row.is_current) || rows[0];
  expect(current?.year_id).toBeTruthy();
  return current.year_id;
}

test('Grade Scale wizard persists complete bands and verifies committed scale', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  const yearId = await currentAcademicYearId(page);
  await page.goto(`${frontendUrl}/grade-scale-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /configure scale/i })).toBeVisible();

  await page.getByPlaceholder(/paste uuid/i).fill(yearId);
  await page.getByPlaceholder(/letter scale/i).fill('E2E Letter Scale');
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/grade-scale-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next: define bands/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /grade bands/i })).toBeVisible();
  await page.getByPlaceholder('A').fill('P');
  const numericInputs = page.locator('input[type="number"]');
  await numericInputs.nth(0).fill('0');
  await numericInputs.nth(1).fill('100');
  const bandsPromise = page.waitForResponse(r => r.url().includes('/bands/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /next: term weights/i }).click();
  expect((await bandsPromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /term weights/i })).toBeVisible();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /commit grade scale/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: /grade scale committed/i })).toBeVisible();
  await expect(page.getByText('E2E Letter Scale')).toBeVisible();
  await expect(page.getByText(/scale id/i)).not.toContainText('—');
});

test('Grade Scale wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/grade-scale-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/grade-scale-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /configure scale/i })).toHaveCount(0);
});