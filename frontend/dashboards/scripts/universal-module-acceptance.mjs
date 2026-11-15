// Real local presenter transactions, ordinary login, no response mocks.
import { chromium, expect } from '@playwright/test';
import { writeFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
const f = JSON.parse(process.env.CROWN_UNIVERSAL_BROWSER_FIXTURE || '{}');
const front = 'http://127.0.0.1:4179', api = 'http://127.0.0.1:8004';
if (!f.synthetic || f.frontend !== front || f.api !== api) throw new Error('Disposable local module fixture required');
const hidden = new Set(Object.values(f.passwords));
const checks = []; let browser, step = 'launch';
try {
  browser = await chromium.launch({ headless: true, ...(process.env.CROWN_BROWSER_EXECUTABLE ? { executablePath: process.env.CROWN_BROWSER_EXECUTABLE } : {}) });
  async function login(role) {
    step = 'normal_login_' + role;
    const page = await browser.newPage();
    expect((await (await page.request.get(front + '/build.json')).json()).build_sha).toBe(f.source_sha);
    expect((await (await page.request.get(api + '/api/health/')).json()).build_sha).toBe(f.source_sha);
    await page.goto(front + '/login');
    await page.getByLabel('Role', { exact: true }).selectOption(role === 'school_admin' ? 'head_of_school' : role);
    await page.getByLabel('Email', { exact: true }).fill(f.usernames[role]);
    await page.getByLabel('Password', { exact: true }).fill(f.passwords[role]);
    await page.getByRole('button', { name: 'Sign In', exact: true }).click();
    await page.waitForURL(url => url.pathname !== '/login');
    const actor = await page.evaluate(() => ({ access: sessionStorage.getItem('crown.jwt.access'), school: sessionStorage.getItem('crown.school.id') }));
    expect(actor.school).toBe(f.school_id); expect(actor.access).toBeTruthy(); hidden.add(actor.access);
    return { page, headers: { Authorization: 'Bearer ' + actor.access, 'X-School-Id': actor.school } };
  }
  const parent = await login('parent'); const pp = parent.page;
  step = 'aid_parent_submit_and_reload';
  await pp.goto(front + '/parent/financial-aid');
  await pp.getByRole('checkbox', { name: /I confirm all application information is fictional/i }).check();
  await pp.getByRole('button', { name: 'Submit fictional Financial Aid application', exact: true }).click();
  await expect(pp.getByText(/submitted and independently verified/)).toBeVisible();
  await pp.reload(); await expect(pp.getByText('SUBMITTED', { exact: true })).toBeVisible();
  checks.push(step);
  step = 'sgo_family_submit';
  await pp.goto(front + '/jireh-sgo/intake');
  const program = await pp.getByLabel('Partner SGO and program').inputValue();
  await pp.getByRole('checkbox', { name: /I consent to submitting this fictional application/ }).check();
  await pp.getByRole('button', { name: 'Submit fictional application', exact: true }).click();
  await expect(pp.getByText('Persistent application readback', { exact: true })).toBeVisible();
  await pp.reload(); await expect(pp.getByText('Persistent application readback', { exact: true })).toBeVisible();
  const officer = await login('finance_director'); const op = officer.page;
  step = 'sgo_processor_request_correction';
  await op.goto(front + '/jireh-sgo/intake');
  await op.getByLabel('Assigned partner program').selectOption(program);
  await op.getByRole('button', { name: 'Request correction', exact: true }).click();
  await pp.reload();
  await pp.getByLabel('Correct or confirm fictional grade').selectOption('8');
  await pp.getByRole('button', { name: 'Save correction and resubmit', exact: true }).click();
  await expect(pp.getByText(/revision: 3; grade: 8/)).toBeVisible();
  await pp.reload(); await expect(pp.getByText(/revision: 3; grade: 8/)).toBeVisible();
  checks.push('sgo_ui_submit_processor_correct_parent_resubmit_reload');
  const staff = await login('daycare_staff'); const sp = staff.page;
  step = 'daycare_actual_admission_api';
  const admitted = await sp.request.post(api + '/api/v1/aftercare/daycare/attendance/checkin/', {
    headers: staff.headers, data: { site_id: f.care.site_id, room_id: f.care.room_id, child_id: f.care.child_id,
      program_code: 'DAYCARE', request_key: randomUUID() } });
  expect(admitted.status()).toBe(201);
  step = 'daycare_ui_release_and_reload';
  await sp.goto(front + '/diadem/daycare');
  await sp.getByRole('button', { name: 'Review pickup', exact: true }).click();
  await sp.getByLabel('Verified pickup recipient').selectOption({ index: 1 });
  await sp.getByLabel('Identity verification method').selectOption('PERSONALLY_KNOWN');
  await sp.getByRole('checkbox', { name: /I verified this person's identity/ }).check();
  await sp.getByRole('button', { name: 'Confirm verified handoff', exact: true }).click();
  await expect(sp.getByText('No open custody records returned for this center.', { exact: true })).toBeVisible();
  await sp.reload(); await expect(sp.getByText('No open custody records returned for this center.', { exact: true })).toBeVisible();
  checks.push(step);
  const admin = await login('school_admin'); const ap = admin.page;
  step = 'am_ui_checkin_handoff_and_reload';
  await ap.goto(front + '/before-care/roster');
  await ap.getByRole('button', { name: 'Check In', exact: true }).click();
  await ap.getByRole('button', { name: 'Acknowledge School Handoff', exact: true }).click();
  await ap.getByRole('checkbox', { name: /I am the receiving staff member/ }).check();
  await ap.getByRole('button', { name: 'Record School Handoff', exact: true }).click();
  await expect(ap.getByText('Handed off', { exact: true })).toBeVisible();
  await ap.reload(); await expect(ap.getByText('Handed off', { exact: true })).toBeVisible();
  checks.push(step);
  step = 'pm_ui_checkin_pickup_and_reload';
  await ap.goto(front + '/aftercare/roster');
  await ap.getByRole('button', { name: 'Check In', exact: true }).click();
  await ap.getByRole('button', { name: 'Verify Pickup', exact: true }).click();
  await ap.getByRole('combobox', { name: 'Authorized pickup contact' }).click();
  await ap.getByRole('option', { name: /Miriam Reed/ }).click();
  await ap.getByRole('checkbox', { name: /I have checked this person's identity/ }).check();
  await ap.getByRole('button', { name: 'Confirm Checkout', exact: true }).click();
  await expect(ap.getByText('Checked out', { exact: true })).toBeVisible();
  await ap.reload(); await expect(ap.getByText('Checked out', { exact: true })).toBeVisible();
  checks.push(step);
  step = 'camp_blocked_admission_with_persisted_registration';
  await ap.goto(front + '/summer-camp-dashboard/roster');
  await expect(ap.getByText(/Avery Reed/).first()).toBeVisible();
  await ap.reload(); await expect(ap.getByText(/Avery Reed/).first()).toBeVisible();
  const denied = await ap.request.post(api + '/api/v1/summer-camp/attendance/checkin/', {
    headers: admin.headers, data: { student_id: f.care.care_student_id, session_id: f.camp_session_id } });
  expect(denied.status()).toBe(400); checks.push(step);
  writeFileSync(process.env.CROWN_UNIVERSAL_BROWSER_OUTPUT, JSON.stringify({ source_sha: f.source_sha,
    source_dirty: f.source_dirty, school_id: f.school_id, generation: f.generation || 0, checks, camp_full_clearance_supported: false, release_certified: false }, null, 2));
} catch (error) {
  let message = String(error?.stack || error);
  for (const value of hidden) if (value) message = message.split(value).join('[redacted]');
  message = message.replace(/Bearer\s+[^\s"']+/g, 'Bearer [redacted]');
  process.stderr.write(JSON.stringify({ step, message, release_certified: false }) + '\n'); process.exitCode = 1;
} finally { if (browser) await browser.close(); }
