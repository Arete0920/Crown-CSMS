import { expect, test, type Page } from '@playwright/test';

const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';

async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  const roleSelect = page.locator('#login-role').first();
  await expect(roleSelect).toBeVisible();
  await roleSelect.selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test('Attendance Codes wizard performs authenticated configure, stage, commit, and verify against live API', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/attendance-codes-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /attendance policy/i })).toBeVisible();

  const createPromise = page.waitForResponse(
    (response) => response.url().includes('/api/v1/attendance-codes-wizard/sessions/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Continue' }).click();
  const createResponse = await createPromise;
  expect(createResponse.ok(), `session create returned ${createResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /attendance codes/i })).toBeVisible();
  await page.locator('#attendance-codes-json').fill(JSON.stringify([
    { code: 'A', label: 'Absent', excused: false, counts_as_absent: true },
    { code: 'E', label: 'Excused', excused: true, counts_as_absent: true },
  ]));

  const stagePromise = page.waitForResponse(
    (response) => response.url().includes('/stage_codes/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Continue' }).click();
  const stageResponse = await stagePromise;
  expect(stageResponse.ok(), `stage codes returned ${stageResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /review and commit/i })).toBeVisible();
  const commitPromise = page.waitForResponse(
    (response) => response.url().includes('/commit/') && response.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    (response) => response.url().includes('/verify/') && response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /commit and verify/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  const verified = await verifyResponse.json();
  expect(verified.status).toBe('verified');
  expect(verified.active_code_count).toBe(2);
  await expect(page.getByRole('heading', { name: /attendance configuration verified/i })).toBeVisible();
  await expect(page.getByTestId('attendance-verification-result')).toContainText('"active_code_count": 2');
});

test('Attendance Codes wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/attendance-codes-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/attendance-codes-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /attendance policy/i })).toHaveCount(0);
});
