import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { test, expect, type Page, type TestInfo } from '@playwright/test';
import { BUYER_WALKTHROUGH } from '../../src/sandbox/buyerWalkthrough.js';

type RouteResult = {
  persona: string;
  label: string;
  route: string;
  finalUrl: string;
  status: number | null;
  title: string;
  screenshot: string;
};

const results: RouteResult[] = [];
const outputPath = resolve(
  process.cwd(),
  process.env.CROWN_BROWSER_AUTHORITY_OUTPUT || 'test-results/buyer-sandbox-browser-authority.json',
);

function slug(value: string) {
  return value
    .toLowerCase()
    .replace(/^https?:\/\//, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '') || 'root';
}

async function assertCrownVisualAuthority(page: Page) {
  const tokens = await page.evaluate(() => {
    const styles = getComputedStyle(document.documentElement);
    return {
      primaryDeep: styles.getPropertyValue('--crown-primary-deep').trim(),
      surface: styles.getPropertyValue('--crown-surface').trim(),
      text: styles.getPropertyValue('--crown-text').trim(),
      radius: styles.getPropertyValue('--crown-radius-md').trim(),
    };
  });

  expect(tokens.primaryDeep, 'CROWN primary token missing').not.toBe('');
  expect(tokens.surface, 'CROWN surface token missing').not.toBe('');
  expect(tokens.text, 'CROWN text token missing').not.toBe('');
  expect(tokens.radius, 'CROWN radius token missing').not.toBe('');
}

async function assertNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
  expect(overflow.scrollWidth, `horizontal overflow: ${JSON.stringify(overflow)}`).toBeLessThanOrEqual(
    overflow.clientWidth + 2,
  );
}

async function launchPersona(page: Page, label: string) {
  const entry = await page.goto(BUYER_WALKTHROUGH.entryRoute, { waitUntil: 'networkidle' });
  expect(entry?.status() ?? 200).toBeLessThan(400);
  await expect(page).not.toHaveURL(/\/login(?:[/?#]|$)/i);
  await expect(page.getByText('No buyer password')).toBeVisible();
  await expect(page.getByText('Heritage Christian Academy', { exact: true })).toBeVisible();

  const card = page.locator('.sandbox-persona-card').filter({ hasText: label }).first();
  await expect(card, `sandbox persona card missing: ${label}`).toBeVisible();
  await card.getByRole('button', { name: /Start guided/i }).click();
  await page.waitForLoadState('networkidle');
  await expect(page).not.toHaveURL(/\/login(?:[/?#]|$)/i);
  await expect(page).not.toHaveURL(/\/not-authorized(?:[/?#]|$)/i);
  await expect(page).not.toHaveURL(/\/forbidden(?:[/?#]|$)/i);
}

test.describe.serial('CROWN buyer sandbox live browser authority', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
  });

  test.afterAll(() => {
    mkdirSync(dirname(outputPath), { recursive: true });
    writeFileSync(
      outputPath,
      JSON.stringify(
        {
          generatedAt: new Date().toISOString(),
          liveFrontendUrl: process.env.CROWN_LIVE_FRONTEND_URL || null,
          entryRoute: BUYER_WALKTHROUGH.entryRoute,
          school: BUYER_WALKTHROUGH.school,
          routeCount: results.length,
          results,
        },
        null,
        2,
      ),
      'utf8',
    );
  });

  test('records exact deployed frontend build identity', async ({ request }, testInfo) => {
    const response = await request.get('/build.json');
    expect(response.status(), '/build.json must resolve').toBe(200);
    const build = await response.json();
    expect(String(build.build_sha || '')).toMatch(/^[0-9a-f]{40}$/i);
    expect(String(build.deploy_tag || '')).not.toBe('');
    await testInfo.attach('deployed-build-identity.json', {
      body: Buffer.from(JSON.stringify(build, null, 2)),
      contentType: 'application/json',
    });
  });

  for (const journey of BUYER_WALKTHROUGH.journeys) {
    test(`${journey.label}: passwordless launch and full journey`, async ({ page }, testInfo) => {
      const consoleErrors: string[] = [];
      const pageErrors: string[] = [];

      page.on('console', (message) => {
        if (message.type() === 'error') consoleErrors.push(message.text());
      });
      page.on('pageerror', (error) => pageErrors.push(error.message));

      await launchPersona(page, journey.label);
      await assertCrownVisualAuthority(page);
      await assertNoHorizontalOverflow(page);

      for (const route of journey.routes) {
        const response = await page.goto(route, { waitUntil: 'networkidle' });
        const status = response?.status() ?? null;
        if (status !== null) expect(status, `${journey.label} ${route}`).toBeLessThan(400);

        await expect(page).not.toHaveURL(/\/login(?:[/?#]|$)/i);
        await expect(page).not.toHaveURL(/\/not-authorized(?:[/?#]|$)/i);
        await expect(page).not.toHaveURL(/\/forbidden(?:[/?#]|$)/i);
        await expect(page.locator('body')).not.toBeEmpty();
        await assertCrownVisualAuthority(page);
        await assertNoHorizontalOverflow(page);

        const bodyText = (await page.locator('body').innerText()).trim();
        expect(bodyText.length, `${journey.label} ${route} rendered too little content`).toBeGreaterThan(40);

        const screenshotName = `${slug(journey.persona)}--${slug(route)}.png`;
        const screenshot = testInfo.outputPath(screenshotName);
        await page.screenshot({ path: screenshot, fullPage: true });
        await testInfo.attach(screenshotName, { path: screenshot, contentType: 'image/png' });

        results.push({
          persona: journey.persona,
          label: journey.label,
          route,
          finalUrl: page.url(),
          status,
          title: await page.title(),
          screenshot: screenshotName,
        });
      }

      expect(pageErrors, `page errors for ${journey.label}`).toEqual([]);
      expect(consoleErrors, `console errors for ${journey.label}`).toEqual([]);
    });
  }

  test('buyer entry remains usable at mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const response = await page.goto(BUYER_WALKTHROUGH.entryRoute, { waitUntil: 'networkidle' });
    expect(response?.status() ?? 200).toBeLessThan(400);
    await expect(page.getByText('No buyer password')).toBeVisible();
    await assertCrownVisualAuthority(page);
    await assertNoHorizontalOverflow(page);
  });
});
