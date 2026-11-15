// Disposable local application acceptance. No mocked responses or token issuer.
import { chromium, expect } from '@playwright/test';
import { writeFileSync } from 'node:fs';
const front = 'http://127.0.0.1:4178', api = 'http://127.0.0.1:8004';
const fixture = JSON.parse(process.env.CROWN_UNIVERSAL_BROWSER_FIXTURE || '{}');
if (!fixture.synthetic || fixture.api !== api || fixture.frontend !== front) throw new Error('Disposable local fixture required');
const hidden = new Set(Object.values(fixture.passwords));
let step = 'launch', browser;
const proofs = [];
try {
  browser = await chromium.launch({ headless: true, ...(process.env.CROWN_BROWSER_EXECUTABLE ? { executablePath: process.env.CROWN_BROWSER_EXECUTABLE } : {}) });
  async function login(role) {
    step = `normal_login_${role}`;
    const context = await browser.newContext();
    const page = await context.newPage();
    expect((await (await page.request.get(front + '/build.json')).json()).build_sha).toBe(fixture.source_sha);
    const health = await (await page.request.get(api + '/api/health/')).json();
    expect(health.build_sha).toBe(fixture.source_sha); expect(health.db).toBe('ok');
    await page.goto(front + '/login');
    await page.getByLabel('Role', { exact: true }).selectOption(role);
    await page.getByLabel('Email', { exact: true }).fill(fixture.usernames[role]);
    await page.getByLabel('Password', { exact: true }).fill(fixture.passwords[role]);
    await page.getByRole('button', { name: 'Sign In', exact: true }).click();
    await page.waitForURL((url) => url.pathname === '/' + role);
    const actor = await page.evaluate(() => ({ access: sessionStorage.getItem('crown.jwt.access'), school: sessionStorage.getItem('crown.school.id') }));
    expect(actor.school).toBe(fixture.school_id); expect(actor.access).toBeTruthy(); hidden.add(actor.access);
    return { page, context, headers: { Authorization: 'Bearer ' + actor.access, 'X-School-Id': actor.school } };
  }
  async function choose(page, label, name) {
    await page.getByRole('combobox', { name: label }).click();
    await page.getByRole('option', { name }).click();
  }
  let assignment = fixture.assignment_id;
  if (fixture.verify_archived) {
    for (const role of ['parent', 'student']) {
      const actor = await login(role);
      async function emptyWorkspace() {
        if (role === 'parent') await actor.page.getByText("Open my children's classroom records", { exact: true }).click();
        else await actor.page.goto(front + '/academics/student-work');
        await expect(actor.page.getByText('No assignments recorded in this window for this selection.', { exact: true })).toBeVisible();
      }
      await emptyWorkspace(); await actor.page.reload(); await emptyWorkspace();
    }
    proofs.push('operator_classroom_archive_parent_student_reload');
  } else {
  const teacher = await login('teacher');
  const tp = teacher.page; step = 'teacher_prepare_assignment';
  await tp.getByText('Open classroom operations and records', { exact: true }).click();
  const room = tp.getByRole('region', { name: "Today's Classroom", exact: true });
  await room.getByText('Create an assignment', { exact: true }).click();
  await choose(tp, 'Assignment section', /Grade 7 English Language Arts/);
  await choose(tp, 'Assignment category', /Classwork/);
  const title = 'Fictional universal narrative assessment';
  await room.getByLabel('Assignment name', { exact: true }).fill(title);
  await room.getByLabel('Possible points', { exact: true }).fill('20');
  await choose(tp, 'Publication', /Published — visible/);
  step = 'teacher_assignment_write';
  const written = tp.waitForResponse((r) => r.url().includes('/assignments/') && r.request().method() === 'POST');
  await room.getByRole('button', { name: 'Save assignment', exact: true }).click();
  const created = await written; expect(created.status()).toBe(201);
  assignment = (await created.json()).id;
  await tp.reload(); await tp.getByText('Open classroom operations and records', { exact: true }).click();
  await expect(tp.getByRole('heading', { name: title, exact: true })).toBeVisible();
  proofs.push('teacher_ui_create_and_reload');
  const student = await login('student');
  const sp = student.page;
  await sp.goto(front + '/academics/student-work');
  const studentCard = () => sp.locator('.MuiCard-root').filter({ has: sp.getByRole('heading', { name: title, exact: true }) });
  await studentCard().getByRole('button', { name: 'Open work and feedback', exact: true }).click();
  const work = 'Fictional learner evidence: a clear narrative explains observations.';
  await studentCard().getByLabel('Your work', { exact: true }).fill(work);
  step = 'student_draft_write';
  await studentCard().getByRole('button', { name: 'Save draft', exact: true }).click();
  await expect(studentCard().getByRole('status')).toContainText('Draft saved');
  await sp.reload();
  await studentCard().getByRole('button', { name: 'Open work and feedback', exact: true }).click();
  await expect(studentCard().getByLabel('Your work', { exact: true })).toHaveValue(work);
  step = 'student_submission';
  await studentCard().getByRole('button', { name: 'Submit work', exact: true }).click();
  await expect(studentCard().getByRole('status')).toContainText('Submission confirmed');
  await sp.reload();
  await expect(studentCard().getByText('Submitted — awaiting grading', { exact: true })).toBeVisible();
  proofs.push('student_ui_draft_submit_and_reload');
  await tp.reload(); await tp.getByText('Open classroom operations and records', { exact: true }).click();
  const teacherCard = tp.locator('.MuiCard-root').filter({ has: tp.getByRole('heading', { name: title, exact: true }) });
  await teacherCard.getByRole('button', { name: 'Open work and feedback', exact: true }).click();
  await choose(tp, 'Student work', 'Avery Reed');
  const feedback = 'Fictional teacher feedback: explain the supporting evidence.';
  await teacherCard.getByLabel('Feedback or revision instructions', { exact: true }).fill(feedback);
  step = 'teacher_feedback';
  await teacherCard.getByRole('button', { name: 'Record feedback', exact: true }).click();
  await expect(teacherCard.getByRole('status')).toContainText('Teacher response recorded');
  const parent = await login('parent');
  await parent.page.getByText("Open my children's classroom records", { exact: true }).click();
  async function parentReadback() {
    const card = parent.page.locator('.MuiCard-root').filter({ has: parent.page.getByRole('heading', { name: title, exact: true }) });
    await card.getByRole('button', { name: 'Open work and feedback', exact: true }).click();
    await expect(card.getByText(feedback, { exact: true })).toBeVisible();
  }
  step = 'parent_downstream_reload';
  await parentReadback(); await parent.page.reload();
  await parent.page.getByText("Open my children's classroom records", { exact: true }).click(); await parentReadback();
  proofs.push('parent_downstream_feedback_and_reload');
  step = 'role_and_tenant_denials';
  const submissions = await sp.request.get(api + '/api/v1/academics/submissions/?assignment_id=' + assignment, { headers: student.headers });
  expect(submissions.status()).toBe(200);
  const saved = await submissions.json();
  const submission = (saved.results || saved)[0].submission_id;
  const denied = await parent.page.request.post(api + '/api/v1/academics/grades/grade/', { headers: parent.headers, data: { submission_id: submission, numeric_score: '18' } });
  expect(denied.status()).toBe(403);
  const foreign = await sp.request.get(api + '/api/v1/academics/classroom/workspace/?audience=student', { headers: { ...student.headers, 'X-School-Id': fixture.foreign_school_id } });
  expect(foreign.status()).toBe(404);
  proofs.push('foreign_school_and_parent_write_denied');
  }
  writeFileSync(process.env.CROWN_UNIVERSAL_BROWSER_OUTPUT, JSON.stringify({ source_sha: fixture.source_sha, source_dirty: fixture.source_dirty, assignment_id: assignment, checks: proofs, release_certified: false }, null, 2));
  console.log(JSON.stringify({ checks_passed: proofs.length, release_certified: false }));
} catch (error) {
  let detail = String(error.stack || error);
  for (const value of hidden) if (value) detail = detail.replaceAll(value, '[redacted]');
  console.error(JSON.stringify({ step, error: detail.replace(/Bearer [A-Za-z0-9._-]+/g, 'Bearer [redacted]'), release_certified: false }));
  process.exitCode = 1;
} finally { if (browser) await browser.close(); }
