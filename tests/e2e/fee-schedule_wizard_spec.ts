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

test('Fee Schedule wizard creates, commits, and verifies a persisted schedule', async ({ page }) => {
  await launchHeritageRole(page, 'finance_director');
  await page.goto(`${frontendUrl}/fee-schedule-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /step 1 of 2.*schedule details/i })).toBeVisible();

  await page.getByLabel(/schedule name/i).fill('Heritage 2026 Fee Schedule E2E');
  await page.getByLabel(/^term/i).fill('2026-2027-E2E');
  await page.getByLabel(/effective date/i).fill('2026-08-15');

  const createPromise = page.waitForResponse(
    (response) => response.url().includes('/api/v1/fee-schedule-wizard/sessions/') && response.request().method() === 'POST',
  );
  const configurePromise = page.waitForResponse(
    (response) => response.url().includes('/configure/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: /next: fee lines/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok(), `create returned ${createResponse.status()}`).toBeTruthy();
  expect(configureResponse.ok(), `configure returned ${configureResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /step 2 of 2.*fee lines/i })).toBeVisible();
  await page.getByLabel(/^code/i).fill('TECH-E2E');
  await page.getByLabel(/^label/i).fill('Technology Fee E2E');
  await page.getByLabel(/amount \(cents\)/i).fill('27500');
  await page.getByLabel(/^kind/i).selectOption('fee');
  await page.getByLabel(/^frequency/i).selectOption('annual');
  await page.getByLabel(/required/i).check();

  const linesPromise = page.waitForResponse(
    (response) => response.url().includes('/lines/') && response.request().method() === 'POST',
  );
  const commitPromise = page.waitForResponse(
    (response) => response.url().includes('/commit/') && response.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    (response) => response.url().includes('/verify/') && response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /commit schedule/i }).click();
  const [linesResponse, commitResponse, verifyResponse] = await Promise.all([linesPromise, commitPromise, verifyPromise]);
  expect(linesResponse.ok(), `lines returned ${linesResponse.status()}`).toBeTruthy();
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /fee schedule created/i })).toBeVisible();
  await expect(page.getByText('Heritage 2026 Fee Schedule E2E')).toBeVisible();
  await expect(page.getByText('2026-2027-E2E')).toBeVisible();
  await expect(page.getByRole('listitem').filter({ hasText: /total lines:/i })).toContainText('1');
  await expect(page.getByRole('listitem').filter({ hasText: /schedule id:/i })).not.toContainText('undefined');
});

test('Fee Schedule wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/fee-schedule-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/fee-schedule-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /schedule details/i })).toHaveCount(0);
});
