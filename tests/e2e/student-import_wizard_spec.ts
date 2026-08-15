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

test('Student Import wizard configures, previews, commits, and verifies a live import row', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/student-import-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /step 1.*configure import/i })).toBeVisible();

  const externalId = `e2e-student-${Date.now()}`;
  const textareas = page.locator('textarea');
  await expect(textareas).toHaveCount(2);
  await textareas.nth(1).fill(JSON.stringify([
    { FirstName: 'E2E', LastName: 'Student', Grade: '9', ExternalId: externalId },
  ], null, 2));

  const createPromise = page.waitForResponse(
    r => r.url().includes('/api/v1/student-import-wizard/sessions/') && r.request().method() === 'POST',
  );
  const configurePromise = page.waitForResponse(
    r => r.url().includes('/configure/') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: /configure import/i }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok(), `create returned ${createResponse.status()}`).toBeTruthy();
  expect(configureResponse.ok(), `configure returned ${configureResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: /step 2.*preview/i })).toBeVisible();
  const previewPromise = page.waitForResponse(
    r => r.url().includes('/preview/') && r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: /run preview/i }).click();
  const previewResponse = await previewPromise;
  expect(previewResponse.ok(), `preview returned ${previewResponse.status()}`).toBeTruthy();
  const preview = await previewResponse.json();
  expect(preview.status).toBe('previewed');
  expect(preview.valid).toBe(1);
  expect(preview.errors).toEqual([]);

  await expect(page.getByRole('heading', { name: /step 3.*commit/i })).toBeVisible();
  await expect(page.locator('pre')).toContainText('"valid": 1');
  const commitPromise = page.waitForResponse(
    r => r.url().includes('/commit/') && r.request().method() === 'POST',
  );
  const verifyPromise = page.waitForResponse(
    r => r.url().includes('/verify/') && r.request().method() === 'GET',
  );
  await page.getByRole('button', { name: /commit and verify/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok(), `commit returned ${commitResponse.status()}`).toBeTruthy();
  expect(verifyResponse.ok(), `verify returned ${verifyResponse.status()}`).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Done' })).toBeVisible();
  const verifiedText = await page.locator('pre').textContent();
  expect(verifiedText).toBeTruthy();
  expect(verifiedText).not.toContain('undefined');
});

test('Student Import wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/student-import-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/student-import-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /configure import/i })).toHaveCount(0);
});
