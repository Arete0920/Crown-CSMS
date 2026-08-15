import { expect, test, type Page } from '@playwright/test';

const frontendUrl = process.env.CERT_FRONTEND_URL || 'http://127.0.0.1:4173';

async function launchHeritageRole(page: Page, role: string) {
  await page.goto(`${frontendUrl}/login`, { waitUntil: 'networkidle' });
  await page.locator('#login-role').first().selectOption(role);
  await page.getByRole('button', { name: /continue to heritage preview/i }).first().click();
  await expect(page).not.toHaveURL(/\/login(?:\?.*)?$/i, { timeout: 30000 });
}

test('Communications wizard drafts, stages, queues, and verifies a live campaign', async ({ page }) => {
  await launchHeritageRole(page, 'admin');
  await page.goto(`${frontendUrl}/comms-setup`, { waitUntil: 'networkidle' });
  await expect(page.getByRole('heading', { name: /purpose & channels/i })).toBeVisible();

  await page.getByRole('button', { name: 'Continue' }).click();
  await expect(page.locator('.crown-alert')).toContainText('Purpose is required');
  await page.locator('#comms-purpose').fill('E2E family communication');
  const createPromise = page.waitForResponse(r => r.url().includes('/api/v1/comms-wizard/sessions/') && r.request().method() === 'POST');
  const configurePromise = page.waitForResponse(r => r.url().includes('/configure/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue' }).click();
  const [createResponse, configureResponse] = await Promise.all([createPromise, configurePromise]);
  expect(createResponse.ok()).toBeTruthy();
  expect(configureResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Message' })).toBeVisible();
  await page.locator('#comms-subject').fill('E2E Heritage Notice');
  await page.locator('#comms-message-body').fill('This is a certification message for the Heritage sandbox.');
  const draftPromise = page.waitForResponse(r => r.url().includes('/message/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: 'Continue' }).click();
  expect((await draftPromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Recipients' })).toBeVisible();
  await page.getByPlaceholder('parent@example.com').fill('parent.reed@heritage.example.org');
  await page.getByPlaceholder('John Smith').fill('Heritage Parent');
  const recipientsPromise = page.waitForResponse(r => r.url().includes('/recipients/') && r.request().method() === 'POST');
  await page.getByRole('button', { name: /continue/i }).click();
  expect((await recipientsPromise).ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Preview' })).toBeVisible();
  await expect(page.getByText('E2E Heritage Notice')).toBeVisible();
  await page.getByRole('button', { name: /proceed to commit|continue/i }).click();

  await expect(page.getByRole('heading', { name: 'Commit' })).toBeVisible();
  await page.getByText(/i confirm this campaign/i).click();
  const commitPromise = page.waitForResponse(r => r.url().includes('/commit/') && r.request().method() === 'POST');
  const verifyPromise = page.waitForResponse(r => r.url().includes('/verify/') && r.request().method() === 'GET');
  await page.getByRole('button', { name: /queue messages/i }).click();
  const [commitResponse, verifyResponse] = await Promise.all([commitPromise, verifyPromise]);
  expect(commitResponse.ok()).toBeTruthy();
  expect(verifyResponse.ok()).toBeTruthy();

  await expect(page.getByRole('heading', { name: 'Verified' })).toBeVisible();
  await expect(page.getByText(/campaign queued and verified/i)).toBeVisible();
  await expect(page.getByText(/messages queued/i)).toBeVisible();
});

test('Communications wizard denies an unauthorized Heritage Teacher', async ({ page }) => {
  await launchHeritageRole(page, 'teacher');
  await page.goto(`${frontendUrl}/comms-setup`, { waitUntil: 'networkidle' });
  await expect(page).not.toHaveURL(/\/comms-setup(?:$|\?)/i);
  await expect(page.getByRole('heading', { name: /purpose & channels/i })).toHaveCount(0);
});
