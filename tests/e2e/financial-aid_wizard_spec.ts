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

test('Financial Aid wizard configures buckets, commits an aid cycle, and verifies live backend state', async ({ page }) => {
  await launchHeritageRole(page, 'school_admin');
  await page.goto(`${frontendUrl}/aid-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /aid year/i })).toBeVisible();

  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.locator('.crown-alert--error')).toContainText('Aid year is required');

  await page.locator('input[placeholder="e.g. 2026-2027"]').fill('2026-2027-E2E');
  const createPromise = page.waitForResponse(
    (response) => response.url().includes('/api/v1/aid-wizard/sessions/') && response.request().method() === 'POST',
  );
  const configurePromise = page.waitForResponse(
    (response) => response.url().includes('/configure/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Continue' }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok(), `create returned ${createResponse.status()}`).toBeTruthy();
  expect(configureResponse.ok(), `configure returned ${configureResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /aid buckets/i })).toBeVisible();
  await page.locator('input[type="checkbox"][value="need"]').check();
  await page.locator('input[type="checkbox"][value="mission"]').check();
  const bucketsPromise = page.waitForResponse(
    (response) => response.url().includes('/buckets/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Continue' }).click();
  const bucketsResponse = await bucketsPromise;
  expect(bucketsResponse.ok(), `buckets returned ${bucketsResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /stage awards/i })).toBeVisible();
  const awardsPromise = page.waitForResponse(
    (response) => response.url().includes('/awards/') && response.request().method() === 'POST',
  );
  await page.getByRole('button', { name: /no awards.*skip/i }).click();
  const awardsResponse = await awardsPromise;
  expect(awardsResponse.ok(), `awards staging returned ${awardsResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Preview' })).toBeVisible();
  await expect(page.getByText('2026-2027-E2E')).toBeVisible();
  await expect(page.getByText(/need, mission/i)).toBeVisible();
  await expect(page.getByText(/no awards staged/i)).toBeVisible();
  await page.getByRole('button', { name: /proceed to commit/i }).click();

  await expect(page.getByRole('heading', { name: /commit aid setup/i })).toBeVisible();
  await page.getByText(/i confirm this setup is correct/i).click();
  const commitPromise = page.waitForResponse(
    (response) => response.url().includes('/commit/') && response.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    (response) => response.url().includes('/verify/') && response.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /commit aid setup/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Verify' })).toBeVisible();
  await expect(page.getByText(/financial aid setup complete/i)).toBeVisible();
  await expect(page.getByText(/awards created/i)).toBeVisible();
  await expect(page.getByText(/errors/i)).toBeVisible();
});

test('Financial Aid wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/aid-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/aid-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /aid year/i })).toHaveCount(0);
});
