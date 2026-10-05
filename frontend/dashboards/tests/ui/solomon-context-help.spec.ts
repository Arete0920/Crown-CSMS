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
    } else if (url.pathname === '/api/solomon/guidance/') {
      expect(route.request().method()).toBe('POST');
      const topic = route.request().postDataJSON().topic;
      expect(['onboarding', 'communications']).toContain(topic);
      expect(route.request().postDataJSON()).toEqual({ topic, human_review_acknowledged: true });
      await route.fulfill({ json: { topic, steps: ['Review dates before sending.'], draft: 'General event reminder: complete [date] before use.', source_document: 'docs/solomon/SOLOMON_APPROVED_ASSISTANCE.md', source_section: topic === 'onboarding' ? 'existing-guidance' : topic, title: 'Implementation guidance', guidance: 'Review school roles.', mode: 'curated_guidance', generated_by_ai: false, human_review_required: true } });
    } else if (url.pathname === '/api/solomon/assistance/') {
      expect(route.request().method()).toBe('POST');
      expect(route.request().postDataJSON()).toEqual({ topic: 'communications', human_review_acknowledged: true });
      await route.fulfill({ json: { topic: 'communications', title: 'General AI draft',
        guidance: 'Verify this draft against the maintained source.', steps: ['Review placeholders.'],
        draft: 'General event: [date]', source_document: 'docs/solomon/SOLOMON_APPROVED_ASSISTANCE.md',
        source_section: 'communications', mode: 'generated_guidance', generated_by_ai: true,
        human_review_required: true } });
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
  const staffGuidance = panel.getByRole('region', { name: 'General staff guidance' });
  await expect(staffGuidance.getByRole('button', { name: 'View guidance' })).toBeDisabled();
  await expect(staffGuidance.getByRole('textbox')).toHaveCount(0);
  await staffGuidance.getByRole('checkbox', { name: /I will review/ }).check();
  await staffGuidance.getByRole('button', { name: 'View guidance' }).click();
  await expect(staffGuidance.getByText('Review school roles.')).toBeVisible();
  await staffGuidance.getByRole('combobox', { name: 'Guidance topic' }).selectOption('communications');
  await expect(staffGuidance.getByText('Review school roles.')).toHaveCount(0);
  await expect(staffGuidance.getByRole('button', { name: 'View guidance' })).toBeDisabled();
  await staffGuidance.getByRole('checkbox', { name: /I will review/ }).check();
  await staffGuidance.getByRole('button', { name: 'View guidance' }).click();
  await expect(staffGuidance.getByRole('region', { name: 'Reusable draft' })).toBeVisible();
  await expect(staffGuidance.getByRole('link', { name: 'Read the maintained source' })).toHaveAttribute('href', /#communications$/);
  await staffGuidance.getByRole('button', { name: 'Draft with AI' }).click();
  await expect(staffGuidance.getByText(/AI draft · Verify against/)).toBeVisible();
  await expect(staffGuidance.getByRole('textbox')).toHaveCount(0);
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
