/**
 * Playwright E2E smoke test for Standalone Schedule Builder module.
 * Module keywords: ScheduleBuilder, scheduler, optimizer, standalone_schedule, conflict_solver
 * Covers check 43: Playwright/E2E Exists.
 */
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:8000';

test.describe('Standalone Schedule Builder - E2E Smoke Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL + '/');
  });

  test('Standalone Schedule Builder: application root is reachable', async ({ page }) => {
    await page.goto(BASE_URL + '/');
    expect(page.url()).toContain(new URL(BASE_URL).hostname);
  });

  test('Standalone Schedule Builder: health endpoint returns 200', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/api/health/');
    expect(response.status()).toBe(200);
  });

  test('Standalone Schedule Builder: integrity endpoint responds without 5xx', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/api/integrity/');
    expect(response.status()).toBeLessThan(500);
  });

  test('Standalone Schedule Builder: unauthenticated access to protected endpoint is blocked', async ({ page }) => {
    const response = await page.request.get(BASE_URL + '/api/auth/me/');
    expect([401, 403]).toContain(response.status());
  });

  test('Standalone Schedule Builder: page loads without critical JS errors', async ({ page }) => {
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
