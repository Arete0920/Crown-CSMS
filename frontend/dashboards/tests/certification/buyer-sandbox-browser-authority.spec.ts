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
const actionProofs: string[] = [];
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

  const card = page.locator('.sandbox-persona-card').filter({ has: page.getByText(label, { exact: true }) });
  await expect(card, `sandbox persona card missing: ${label}`).toBeVisible();
  const launchButton = card.getByRole('button', { name: /Start guided/i });
  await Promise.all([
    page.waitForURL(
      (url) => url.pathname !== BUYER_WALKTHROUGH.entryRoute,
      { timeout: 30000 },
    ),
    launchButton.click(),
  ]);
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
          actionProofs,
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


  test('admissions converts an accepted fictional applicant and persists the student handoff', async ({ page }) => {
    await launchPersona(page, 'Admissions Director');
    await page.goto('/admissions/pipeline', { waitUntil: 'networkidle' });
    const targetFamily = 'Mercer Enrollment Conversion Demo Family';
    const row = page.getByRole('row').filter({ hasText: targetFamily }).filter({ hasText: 'Accepted' }).first();
    await expect(row).toBeVisible();
    await row.getByRole('button', { name: 'Open' }).click();
    await expect(page.getByText('Household Admissions Review')).toBeVisible();
    await page.getByRole('button', { name: 'Show details' }).first().click();
    const conversion = page.waitForResponse((response) =>
      response.url().includes('/api/admissions/enroll/') &&
      response.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Enroll Child' }).first().click();
    const response = await conversion;
    expect(response.ok()).toBe(true);
    const enrolled = await response.json();
    expect(enrolled.ok).toBe(true);
    expect(enrolled.student_id).toBeTruthy();
    expect(enrolled.canonical_gate).toBe('contract_countersigned_and_deposit_paid_or_waived');
    await page.reload({ waitUntil: 'networkidle' });
    await expect(page.getByRole('row').filter({ hasText: targetFamily }).filter({ hasText: 'Enrolled' }).first()).toBeVisible();
    actionProofs.push('admissions_conversion_persists');
  });

  test('student workspace shows school data and denies finance and administrative routes', async ({ page }) => {
    await launchPersona(page, 'Student');
    await page.goto('/student', { waitUntil: 'networkidle' });
    await expect(page.getByTestId('sandbox-student-self-service')).toBeVisible();
    await expect(page.getByTestId('student-self-service-name')).toHaveText('Avery Reed');
    await expect(page.getByTestId('student-schedule')).toContainText('Grade 7 English Language Arts');
    await page.reload({ waitUntil: 'networkidle' });
    await expect(page.getByTestId('student-learning-tasks')).toContainText('Vocabulary Check 1');
    for (const route of ['/finance', '/school-admin-dashboard']) {
      await page.goto(route, { waitUntil: 'domcontentloaded' });
      expect(new URL(page.url()).pathname).not.toBe(route);
    }
    actionProofs.push('student_role_denials_and_workflow');
  });

  test('finance manual demonstration payment persists after reload', async ({ page }) => {
    await launchPersona(page, 'Finance Director');
    await page.goto('/finance', { waitUntil: 'networkidle' });
    const panel = page.getByTestId('sandbox-finance-transaction');
    await expect(panel).toBeVisible();
    const payment = page.waitForResponse((response) =>
      response.url().includes('/api/v1/sandbox/finance/apply-payment/') &&
      response.request().method() === 'POST',
    );
    await panel.getByRole('button', { name: 'Apply Demo Payment' }).click();
    const response = await payment;
    expect(response.status()).toBe(200);
    const payload = await response.json();
    expect(payload.reconciliation_status).toBe('reconciled');
    expect(payload.external_payment_processed).toBe(false);
    expect(payload.over_refund_blocked).toBe(true);
    await page.reload({ waitUntil: 'networkidle' });
    await expect(page.getByTestId('finance-reconciliation')).toHaveText('reconciled');
    await expect(page.getByTestId('finance-remaining')).toHaveText('$0.00');
    actionProofs.push('finance_manual_payment_persists');
  });

  test('teacher lesson plan persists with fictional classroom data', async ({ page }) => {
    await launchPersona(page, 'Teacher / Staff');
    await page.goto('/teacher/lesson-plans/today', { waitUntil: 'networkidle' });
    await expect(page.getByTestId('teacher-lesson-plan-editor')).toBeVisible();
    const select = page.getByLabel('Lesson plan section');
    await expect(select.locator('option')).toHaveCount(2);
    await select.selectOption({ index: 1 });
    const proof = 'Heritage sales rehearsal lesson proof';
    await page.getByLabel('Learning objectives').fill(proof);
    await page.getByLabel('Materials and curriculum resources').fill('Fictional curriculum resource');
    await page.getByLabel('Instructional activities').fill('Read, discuss and respond');
    await page.getByLabel('Homework').fill('Write a paragraph');
    await page.getByLabel('Private teacher notes').fill('Local sales readiness proof');
    const save = page.waitForResponse((response) =>
      response.url().includes('/lesson-plans/') && response.request().method() !== 'GET',
    );
    await page.getByRole('button', { name: /save lesson plan/i }).click();
    expect((await save).ok()).toBe(true);
    await expect(page.getByRole('status')).toContainText(/lesson plan saved/i);
    await page.reload({ waitUntil: 'networkidle' });
    await expect(page.getByLabel('Learning objectives')).toHaveValue(proof);
    await expect(page.getByLabel('Private teacher notes')).toHaveValue('Local sales readiness proof');
    actionProofs.push('teacher_lesson_plan_persists');
  });

  test('parent enrollment agreement completes the fictional student handoff', async ({ page }) => {
    await launchPersona(page, 'Parent / Guardian');
    await page.goto('/parent/admissions/status', { waitUntil: 'networkidle' });
    const panel = page.getByTestId('sandbox-parent-enrollment-panel');
    await expect(panel).toBeVisible();
    await expect(panel).toContainText('Jordan Reed');
    await page.getByLabel('Accept sandbox enrollment agreement').check();
    const completion = page.waitForResponse((response) =>
      response.url().includes('/api/v1/sandbox/parent/enrollment/') &&
      response.request().method() === 'POST',
    );
    await page.getByRole('button', { name: /accept enrollment and complete demo handoff/i }).click();
    const response = await completion;
    expect(response.ok()).toBe(true);
    const payload = await response.json();
    expect(payload.lifecycle_stage).toBe('enrolled');
    expect(payload.applicant_to_student_status).toBe('completed');
    expect(payload.demo_payment_processed).toBe(false);
    await expect(page.getByTestId('sandbox-parent-enrollment-complete')).toContainText('Jordan Reed');
    actionProofs.push('parent_enrollment_handoff_completed');
  });

  test('buyer entry remains usable at mobile width', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const response = await page.goto(BUYER_WALKTHROUGH.entryRoute, { waitUntil: 'networkidle' });
    expect(response?.status() ?? 200).toBeLessThan(400);
    await expect(page.getByText('No buyer password')).toBeVisible();
    await assertCrownVisualAuthority(page);
    await assertNoHorizontalOverflow(page);
  });
});
