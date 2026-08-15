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

test('Staff Onboarding wizard previews, commits, and verifies a live staff record', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/staff-onboarding`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /step 1.*staff details/i })).toBeVisible();

  const uniqueEmail = `e2e.staff.${Date.now()}@heritage.example.org`;
  await page.getByLabel(/first name/i).fill('E2E');
  await page.getByLabel(/last name/i).fill('Teacher');
  await page.getByLabel(/^email/i).fill(uniqueEmail);
  await page.getByLabel(/^role/i).selectOption('TEACHER');

  const createPromise = page.waitForResponse(
    r => r.url().includes('/api/v1/staff-onboarding-wizard/sessions/') && r.request().method() === 'POST',
  );
  const configurePromise = page.waitForResponse(
    r => r.url().includes('/configure/') && r.request().method() === 'POST',
  );
  const previewPromise = page.waitForResponse(
    r => r.url().includes('/preview/') && r.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /preview/i }).click();
  const [createResponse, configureResponse, previewResponse] = await Promise.all([createPromise, configurePromise, previewPromise]);
  expect(createResponse.ok(), `create returned ${createResponse.status()}`).toBeTruthy();
  expect(configureResponse.ok(), `configure returned ${configureResponse.status()}`).toBeTruthy();
  expect(previewResponse.ok(), `preview returned ${previewResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /step 2.*preview/i })).toBeVisible();
  await expect(page.getByText(uniqueEmail)).toBeVisible();
  const commitPromise = page.waitForResponse(
    r => r.url().includes('/commit/') && r.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    r => r.url().includes('/verify/') && r.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /confirm.*create staff/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Done' })).toBeVisible();
  await expect(page.getByText(uniqueEmail)).toBeVisible();
  await expect(page.getByText('TEACHER', { exact: true })).toBeVisible();
  await expect(page.getByText(/staff id/i)).toBeVisible();
});

test('Staff Onboarding wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/staff-onboarding`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/staff-onboarding(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /staff details/i })).toHaveCount(0);
});
