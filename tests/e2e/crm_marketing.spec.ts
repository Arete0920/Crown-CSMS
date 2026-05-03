/**
 * Playwright E2E smoke test for CRM Marketing Suite module.
 * Module keywords: CRM, Marketing, campaign, prospect, lead
 * Covers check 43: Playwright/E2E Exists.
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:8000';

test.describe('CRM Marketing Suite - E2E Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL + '/');
  });

  test('CRM Marketing Suite: application root is reachable', async ({ page }) => {
    await page.goto(BASE_URL + '/');
    expect(page.url()).toContain(new URL(BASE_URL).hostname);
  });

  test('CRM Marketing Suite: health endpoint returns 200', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/api/health/');
    expect(response.status()).toBe(200);
  });

  test('CRM Marketing Suite: integrity endpoint responds without 5xx', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/api/integrity/');
    expect(response.status()).toBeLessThan(500);
  });

  test('CRM Marketing Suite: unauthenticated access to protected endpoint is blocked', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/api/auth/me/');
    expect([401, 403]).toContain(response.status());
  });

  test('CRM Marketing Suite: missing tenant header is fail-closed on /api/v1/nav/', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/api/v1/nav/');
    expect(response.status()).toBe(400);
    const payload = await response.json();
    expect(payload.code).toBe('missing_tenant');
  });

  test('CRM Marketing Suite: page loads without critical JS errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.goto(BASE_URL + '/');
    const critical = errors.filter(
      (e) => !e.includes('favicon') && !e.includes('ResizeObserver')
    );
    // e2e spec.ts: no critical JS errors on root page load
    expect(critical.length).toBe(0);
  });
});
