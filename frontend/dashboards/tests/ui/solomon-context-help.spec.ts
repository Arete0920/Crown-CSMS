import { test, expect } from '@playwright/test';

// UI contract proof with stubbed published guidance; not deployed-content certification.
test('Solomon help supports native keyboard dismissal, focus return and mobile reduced motion', async ({ page }) => {
  await page.addInitScript(() => {
    for (const storage of [sessionStorage, localStorage]) {
      storage.setItem('crown.jwt.access', 'playwright-demo-token');
      storage.setItem('crown.role', 'finance');
      storage.setItem('crown.school.id', '19801b59-8c05-4c84-9312-5d792e4e839d');
    }
  });
  let helpRequests = 0;
  await page.route('**/api/**', async route => {
    const url = new URL(route.request().url());
    if (url.pathname === '/api/v1/solomon/context/') {
      helpRequests += 1;
      expect(url.searchParams.get('route_path')).toBe('/billing');
      expect(url.searchParams.get('module')).toBe('billing');
      await route.fulfill({ json: { primary_article: { title: 'Review billing before posting', content: 'Confirm the billing period and review invoice totals.' } } });
    } else {
      await route.fulfill({ json: {} });
    }
  });
  await page.goto('/billing');
  const trigger = page.getByRole('button', { name: 'Help from Solomon' }).first();
  await expect(trigger).toBeVisible();
  expect(helpRequests).toBe(0);
  await trigger.click();
  const panel = page.getByRole('dialog');
  await expect(panel.getByRole('heading', { name: 'Review billing before posting' })).toBeVisible();
  await panel.getByRole('button', { name: 'Meet Solomon' }).click();
  await expect(panel.getByRole('heading', { name: 'Meet Solomon' })).toBeVisible();
  const back = panel.getByRole('button', { name: 'Back to page help' });
  await expect(back).toBeFocused();
  await back.click();
  await expect(panel.getByRole('button', { name: 'Meet Solomon' })).toBeFocused();
  await expect(panel.getByRole('heading', { name: 'Review billing before posting' })).toBeVisible();
  expect(helpRequests).toBe(1);
  await page.keyboard.press('Escape');
  await expect(panel).not.toBeVisible();
  await expect(trigger).toBeFocused();
  await page.setViewportSize({ width: 375, height: 667 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await trigger.click();
  await expect(panel.getByRole('heading', { name: 'Review billing before posting' })).toBeVisible();
  const bounds = await panel.boundingBox();
  expect(bounds).not.toBeNull();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(375);
  expect(await panel.evaluate(el => getComputedStyle(el).animationName)).toBe('none');
  await panel.getByRole('button', { name: 'Close help' }).click();
  await expect(trigger).toBeFocused();
});
