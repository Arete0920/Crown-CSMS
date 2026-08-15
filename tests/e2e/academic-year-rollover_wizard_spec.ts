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

test('Academic Year Rollover creates terms, commits, and verifies persisted current-year state', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/academic-year-rollover`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /step 1 of 2.*year details/i })).toBeVisible();

  await page.getByLabel(/year name/i).fill('2031-2032-E2E');
  await page.getByLabel(/^start date/i).fill('2031-08-15');
  await page.getByLabel(/^end date/i).fill('2032-06-15');

  const createPromise = page.waitForResponse(
    (response) => response.url().includes('/api/v1/academic-year-wizard/sessions/') && response.request().method() === 'POST',
  );
  const configurePromise = page.waitForResponse(
    (response) => response.url().includes('/configure/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: /next: define terms/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok(), `create returned ${createResponse.status()}`).toBeTruthy();
  expect(configureResponse.ok(), `configure returned ${configureResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /step 2 of 2.*academic terms/i })).toBeVisible();
  await page.getByLabel(/^code/i).fill('FALL-2031-E2E');
  await page.getByLabel(/^name/i).fill('Fall 2031 E2E');
  await page.getByLabel(/school year/i).fill('2031-32-E2E');
  await page.getByLabel(/^start date/i).fill('2031-08-15');
  await page.getByLabel(/^end date/i).fill('2031-12-20');

  const termsPromise = page.waitForResponse(
    (response) => response.url().includes('/terms/') && response.request().method() === 'POST',
  );
  const commitPromise = page.waitForResponse(
    (response) => response.url().includes('/commit/') && response.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    (response) => response.url().includes('/verify/') && response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /commit rollover/i }).click();
  const [termsResponse, commitResponse, verifyResponse] = await Promise.all([termsPromise, commitPromise, verifyPromise]);
  expect(termsResponse.ok(), `terms returned ${termsResponse.status()}`).toBeTruthy();
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /academic year created/i })).toBeVisible();
  await expect(page.getByText('2031-2032-E2E')).toBeVisible();
  await expect(page.getByText(/is current:/i)).toContainText('Yes');
  await expect(page.getByText(/total terms:/i)).toContainText('1');
  await expect(page.getByText(/year id:/i)).not.toContainText('undefined');
});

test('Academic Year Rollover denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/academic-year-rollover`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/academic-year-rollover(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /year details/i })).toHaveCount(0);
});
