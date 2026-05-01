import { test, expect } from '@playwright/test';
const baseUrl = process.env.CROWN_FRONTEND_BASE_URL || 'https://yellow-forest-0eecc8b0f.7.azurestaticapps.net';
test('CROWN frontend root loads without hard 404', async ({ page }) => {
  const response = await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  expect(response?.status(), 'root status').toBeLessThan(400);
  await expect(page.locator('body')).toBeVisible();
});
test('CROWN frontend has no obvious empty body', async ({ page }) => {
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
  const text = (await page.locator('body').innerText()).trim();
  expect(text.length, 'body text length').toBeGreaterThan(20);
});
test('CROWN frontend has no console errors on root load', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  expect(errors, 'console errors').toEqual([]);
});
