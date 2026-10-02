import { test, expect } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:8000';

test.describe('CROWN platform integrity smoke', () => {
  test('application root is reachable without critical JavaScript errors', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', (err) => errors.push(err.message));
    await page.goto(BASE_URL + '/');
    expect(page.url()).toContain(new URL(BASE_URL).hostname);
    const critical = errors.filter(
      (error) => !error.includes('favicon') && !error.includes('ResizeObserver')
    );
    expect(critical).toEqual([]);
  });

  test('health endpoint returns 200', async ({ request }) => {
    const response = await request.get(BASE_URL + '/api/health/');
    expect(response.status()).toBe(200);
  });

  test('integrity endpoint does not return a server error', async ({ request }) => {
    const response = await request.get(BASE_URL + '/api/integrity/');
    expect(response.status()).toBeLessThan(500);
  });

  test('unauthenticated protected access is denied', async ({ request }) => {
    const response = await request.get(BASE_URL + '/api/auth/me/');
    expect([401, 403]).toContain(response.status());
  });

  test('tenant-scoped navigation fails closed without tenant context', async ({ request }) => {
    const response = await request.get(BASE_URL + '/api/v1/nav/');
    expect(response.status()).toBe(400);
    const payload = await response.json();
    expect(payload.code).toBe('missing_tenant');
  });

  test('invalid tenant context cannot return successful navigation data', async ({ request }) => {
    const response = await request.get(BASE_URL + '/api/v1/nav/', {
      headers: { 'X-School-Id': '99999' },
    });
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });
});
