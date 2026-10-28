import assert from 'node:assert/strict';
import { Buffer } from 'node:buffer';
import { execFileSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { createContext, EvidenceCollector, EXPORTER_FILES, PHASES, validateReport } from './browser-evidence-schema.mjs';
import { executeSuite, validateCandidate } from './run-dev-browser-evidence.mjs';

const PROJECT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MARKER = 'SYNTHETIC_PRIVATE_AUTH_SCHOOL_MARKER_DO_NOT_EXPORT';
const SOURCE = 'a'.repeat(40);

function context(phase = 'buyer') {
  const definitions = [
    ...EXPORTER_FILES.map(file => [file, 'exporter']),
    ...['playwright.config.ts', 'package.json', 'package-lock.json'].map(file => [file, 'runtime']),
    [PHASES[phase], 'test'],
  ];
  return {
    schema_version: 1, repository: 'Arete0920/Crown-CSMS', run_id: '123', run_attempt: 2,
    phase, invocation_nonce: 'b'.repeat(64),
    source: { runtime_sha: SOURCE, test_sha: SOURCE, exporter_sha: SOURCE },
    files: definitions.map(([file, role]) => ({
      path: `frontend/dashboards/${file}`, role, source_sha: SOURCE, blob_sha: SOURCE,
      sha256: 'c'.repeat(64), bytes: 100,
      test_locations: role === 'test' ? [{ line: 3, column: 1 }] : [],
    })),
  };
}

function result(overrides = {}) {
  return {
    retry: 0, status: 'passed', duration: 12, errors: [],
    attachments: [], stdout: [], stderr: [], ...overrides,
  };
}

function testCase(ctx, observation = result()) {
  return {
    location: { file: path.join(PROJECT, PHASES[ctx.phase]), line: 3, column: 1 },
    expectedStatus: 'passed', results: [observation], outcome: () => 'expected',
    title: MARKER, id: MARKER, annotations: [{ type: MARKER, description: MARKER }],
  };
}
function fullResult(status = 'passed') { return { status, startTime: new Date('2026-10-28T00:00:00Z'), duration: 50 }; }
function reportFor(ctx = context()) {
  const observation = result(); const item = testCase(ctx, observation);
  const collector = new EvidenceCollector(ctx, PROJECT);
  collector.begin([item]); collector.endTest(item, observation);
  return collector.finish(fullResult());
}

function fixture(t, specs = {}) {
  const root = mkdtempSync(path.join(os.tmpdir(), 'crown-browser-evidence-test-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const projectDirectory = path.join(root, 'frontend/dashboards');
  for (const relative of [...EXPORTER_FILES, 'playwright.config.ts', 'package.json', 'package-lock.json']) {
    const target = path.join(projectDirectory, relative);
    mkdirSync(path.dirname(target), { recursive: true });
    copyFileSync(path.join(PROJECT, relative), target);
  }
  const basic = "import { test } from '@playwright/test';\ntest('synthetic no-browser execution', () => {});\n";
  for (const [phase, relative] of Object.entries(PHASES)) {
    const target = path.join(projectDirectory, relative);
    mkdirSync(path.dirname(target), { recursive: true });
    writeFileSync(target, specs[phase] ?? basic);
  }
  const git = args => execFileSync('git', args, { cwd: root, stdio: ['ignore', 'pipe', 'pipe'] }).toString().trim();
  git(['init', '--quiet']); git(['add', 'frontend']);
  git(['-c', 'user.name=CROWN synthetic test', '-c', 'user.email=synthetic@example.invalid', 'commit', '--quiet', '-m', 'Synthetic evidence fixture']);
  const commit = git(['rev-parse', 'HEAD']);
  symlinkSync(path.join(PROJECT, 'node_modules'), path.join(projectDirectory, 'node_modules'), 'dir');
  const runner = path.join(root, 'runner'); mkdirSync(runner);
  const env = {
    ...process.env, CI: '1', GITHUB_REPOSITORY: 'Arete0920/Crown-CSMS', GITHUB_RUN_ID: '123', GITHUB_RUN_ATTEMPT: '2',
    CROWN_EVIDENCE_RUNTIME_SHA: commit, CROWN_EVIDENCE_TEST_SHA: commit, CROWN_EVIDENCE_EXPORTER_SHA: commit,
    CROWN_LIVE_FRONTEND_URL: 'https://example.invalid', RUNNER_TEMP: runner,
    GITHUB_OUTPUT: path.join(root, 'outputs.txt'),
  };
  return { root, projectDirectory, env, git };
}

test('allowlist export omits hostile titles, errors, headers, bodies and attachments', () => {
  const ctx = context();
  const observation = result({
    errors: [{ message: MARKER, stack: MARKER, value: MARKER }],
    attachments: [{ name: MARKER, body: Buffer.from(MARKER), path: MARKER, contentType: MARKER }],
    stdout: [MARKER], stderr: [Buffer.from(MARKER)],
    headers: { Authorization: MARKER }, storageState: { cookies: [MARKER] }, response: { body: MARKER },
  });
  const item = testCase(ctx, observation);
  Object.defineProperty(item, 'titlePath', { get() { throw new Error(MARKER); } });
  const collector = new EvidenceCollector(ctx, PROJECT);
  collector.begin([item]); collector.endTest(item, observation);
  const report = collector.finish(fullResult());
  assert.equal(JSON.stringify(report).includes(MARKER), false);
  assert.equal(report.cases[0].results[0].error_count, 1);
  assert.equal(report.cases[0].results[0].omitted_attachment_count, 1);
  assert.equal(report.cases[0].results[0].omitted_stdout_chunk_count, 1);
  assert.equal(report.cases[0].case_id, 'buyer:3:1:1');
});

test('unknown source location and invalid callback values poison the report', () => {
  for (const mutate of [
    item => { item.location.file = `/private/${MARKER}.ts`; },
    item => { item.location.column = 2; },
    item => { item.results[0].status = MARKER; },
    item => { item.results[0].duration = Infinity; },
  ]) {
    const ctx = context(); const item = testCase(ctx); mutate(item);
    const collector = new EvidenceCollector(ctx, PROJECT);
    collector.guard(() => collector.begin([item]));
    collector.guard(() => collector.endTest(item, item.results[0]));
    assert.throws(() => collector.finish(fullResult()), /SAFE_BROWSER_EVIDENCE_INVALID/);
  }
});

test('final results reconciliation rejects a dropped retry callback', () => {
  const ctx = context();
  const failed = result({ status: 'failed', errors: [{ message: MARKER }] });
  const passed = result({ retry: 1 });
  const item = testCase(ctx, failed); item.results = [failed, passed]; item.outcome = () => 'flaky';
  const collector = new EvidenceCollector(ctx, PROJECT);
  collector.begin([item]); collector.endTest(item, failed);
  assert.throws(() => collector.finish(fullResult()), /SAFE_BROWSER_EVIDENCE_INVALID/);
  collector.endTest(item, passed);
  const report = collector.finish(fullResult());
  assert.equal(report.cases[0].results.length, 2);
  assert.equal(report.cases[0].outcome, 'flaky');
});

test('runtime expected-status changes are reflected without exporting annotations', () => {
  const ctx = context(); const observation = result({ status: 'failed' }); const item = testCase(ctx, observation);
  const collector = new EvidenceCollector(ctx, PROJECT); collector.begin([item]);
  item.expectedStatus = 'failed'; collector.endTest(item, observation);
  assert.equal(collector.finish(fullResult()).cases[0].expected_status, 'failed');
});

test('external validation rejects an impossible successful status/outcome combination', () => {
  const ctx = context(); const report = reportFor(ctx);
  report.cases[0].results[0].status = 'failed';
  assert.throws(() => validateReport(report, ctx), /SAFE_BROWSER_EVIDENCE_INVALID/);
});

test('bounded outcome consistency retains skip and interrupted semantics', () => {
  for (const [expectedStatus, statuses, outcome] of [
    ['skipped', ['skipped'], 'skipped'],
    ['passed', ['skipped'], 'skipped'],
    ['passed', ['interrupted'], 'skipped'],
    ['skipped', ['failed', 'skipped'], 'flaky'],
  ]) {
    const ctx = context(); const item = testCase(ctx);
    item.expectedStatus = expectedStatus; item.outcome = () => outcome;
    item.results = statuses.map((status, retry) => result({ status, retry }));
    const collector = new EvidenceCollector(ctx, PROJECT); collector.begin([item]);
    for (const observation of item.results) collector.endTest(item, observation);
    assert.equal(collector.finish(fullResult('failed')).cases[0].outcome, outcome);
  }
});

test('all-skipped or interrupted Playwright results cannot publish as a passing suite', () => {
  for (const [expectedStatus, status] of [['skipped', 'skipped'], ['passed', 'interrupted']]) {
    const ctx = context(); const observation = result({ status });
    const item = testCase(ctx, observation);
    item.expectedStatus = expectedStatus; item.outcome = () => 'skipped';
    const collector = new EvidenceCollector(ctx, PROJECT);
    collector.begin([item]); collector.endTest(item, observation);
    assert.throws(() => collector.finish(fullResult()), /SAFE_BROWSER_EVIDENCE_INVALID/);
    assert.equal(collector.finish(fullResult('failed')).cases[0].outcome, 'skipped');
  }
});

test('actual all-skipped Playwright suite is not publishable evidence', async t => {
  const f = fixture(t, { buyer: "import { test } from '@playwright/test';\ntest.skip('skipped', () => {});\n" });
  const result = await executeSuite({ suite: 'buyer', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, false);
  assert.notEqual(result.exitCode, 0);
});

test('external validation rejects stale, absent, truncated, symlink and additional-field reports', t => {
  const root = mkdtempSync(path.join(os.tmpdir(), 'crown-evidence-candidate-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const file = path.join(root, 'candidate.json'); const ctx = context();
  assert.throws(() => validateCandidate(file, ctx));
  writeFileSync(file, '{'); assert.throws(() => validateCandidate(file, ctx));
  const stale = reportFor(ctx); stale.context = { ...ctx, invocation_nonce: 'd'.repeat(64) };
  writeFileSync(file, JSON.stringify(stale)); assert.throws(() => validateCandidate(file, ctx));
  const unsafe = reportFor(ctx); unsafe.error = MARKER;
  assert.throws(() => validateReport(unsafe, ctx));
  writeFileSync(file, JSON.stringify(reportFor(ctx)));
  const link = path.join(root, 'link.json'); symlinkSync(file, link);
  assert.throws(() => validateCandidate(link, ctx));
  assert.equal(validateCandidate(file, ctx).runner_status, 'passed');
});

test('source context verifies exact Git bytes and separates runtime, test and exporter roles', t => {
  const f = fixture(t); const ctx = createContext(f.env, f.projectDirectory, 'buyer');
  assert.deepEqual(new Set(ctx.files.map(file => file.role)), new Set(['runtime', 'test', 'exporter']));
  assert.deepEqual(ctx.files.find(file => file.role === 'test').test_locations, [{ line: 2, column: 1 }]);
  writeFileSync(path.join(f.projectDirectory, PHASES.buyer), `// ${MARKER}\n`);
  assert.throws(() => createContext(f.env, f.projectDirectory, 'buyer'));
});

test('actual Playwright preserves failure while exporting only a constructed report', async t => {
  const f = fixture(t, { buyer: [
    "import { test } from '@playwright/test';",
    `test('${MARKER}', async ({}, info) => {`,
    `  console.log('${MARKER}'); console.error('${MARKER}');`,
    `  await info.attach('${MARKER}', { body: Buffer.from('${MARKER}'), contentType: 'text/plain' });`,
    `  throw new Error('${MARKER}');`,
    '});',
  ].join('\n') });
  const result = await executeSuite({ suite: 'buyer', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, true); assert.equal(result.exitCode, 1);
  assert.deepEqual(readdirSync(result.evidencePath).sort(), ['MANIFEST.json', 'buyer.json']);
  for (const name of readdirSync(result.evidencePath)) assert.equal(readFileSync(path.join(result.evidencePath, name), 'utf8').includes(MARKER), false);
  const report = JSON.parse(readFileSync(path.join(result.evidencePath, 'buyer.json')));
  assert.equal(report.runner_status, 'failed'); assert.equal(report.cases[0].results[0].error_count, 1);
  // Playwright may also attach its own failure context alongside the explicit
  // attachment. Both must be counted without exporting either body.
  assert.ok(report.cases[0].results[0].omitted_attachment_count >= 1);
  assert.deepEqual(readdirSync(path.dirname(result.evidencePath)), ['publish']);
  assert.match(readFileSync(f.env.GITHUB_OUTPUT, 'utf8'), /evidence_valid=true/);
});

test('actual certification preserves preflight failure short circuit', async t => {
  const f = fixture(t, { preflight: `import { test } from '@playwright/test';\ntest('failure', () => { throw new Error('${MARKER}'); });\n` });
  const result = await executeSuite({ suite: 'certification', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, true); assert.equal(result.exitCode, 1);
  assert.deepEqual(result.manifest.phases, [
    { phase: 'preflight', execution: 'completed', runner_exit_code: 1, runner_status: 'failed' },
    { phase: 'crawler', execution: 'not_run_prior_phase_failed' },
  ]);
  assert.equal(existsSync(path.join(result.evidencePath, 'crawler.json')), false);
});

test('actual certification executes both phases on success', async t => {
  const f = fixture(t);
  const result = await executeSuite({ suite: 'certification', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, true); assert.equal(result.exitCode, 0);
  assert.deepEqual(result.manifest.phases.map(phase => phase.phase), ['preflight', 'crawler']);
  assert.deepEqual(readdirSync(result.evidencePath).sort(), ['MANIFEST.json', 'crawler.json', 'preflight.json']);
});

test('actual Playwright retains expected failure, skipped modifiers and retry outcomes', async t => {
  const f = fixture(t, { buyer: [
    "import { test } from '@playwright/test';",
    'test.describe.configure({ retries: 1 });',
    `test('expected failure', () => { test.fail(); throw new Error('${MARKER}'); });`,
    "test.skip('declared skip', () => {});",
    "test.fixme('declared fixme', () => {});",
    `test('retry', ({}, info) => { if (info.retry === 0) throw new Error('${MARKER}'); });`,
  ].join('\n') });
  const result = await executeSuite({ suite: 'buyer', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, true); assert.equal(result.exitCode, 0);
  const report = JSON.parse(readFileSync(path.join(result.evidencePath, 'buyer.json')));
  assert.deepEqual(report.cases.map(item => item.outcome), ['expected', 'skipped', 'skipped', 'flaky']);
  assert.deepEqual(report.cases.map(item => item.expected_status), ['failed', 'skipped', 'skipped', 'passed']);
  assert.deepEqual(report.cases.map(item => item.source.column), [1, 6, 6, 1]);
  assert.equal(report.cases[3].results.length, 2);
  assert.equal(JSON.stringify(report).includes(MARKER), false);
});

test('actual Playwright only modifier binds its public property location', async t => {
  const f = fixture(t, { buyer: "import { test } from '@playwright/test';\ntest.only('only modifier', () => {});\n" });
  const result = await executeSuite({ suite: 'buyer', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, true); assert.equal(result.exitCode, 0);
  const report = JSON.parse(readFileSync(path.join(result.evidencePath, 'buyer.json')));
  assert.equal(report.cases[0].source.column, 6);
});

test('actual passing Playwright cannot publish after a swallowed callback rejection', async t => {
  const f = fixture(t, { buyer: [
    "import { test } from '@playwright/test';",
    "test('allowed source declaration', () => {});",
    'const alias = test;',
    "alias('unrecognized source declaration', () => {});",
  ].join('\n') });
  const result = await executeSuite({ suite: 'buyer', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, false); assert.notEqual(result.exitCode, 0);
  assert.doesNotMatch(readFileSync(f.env.GITHUB_OUTPUT, 'utf8'), /evidence_valid=true|evidence_path=/);
});

test('actual empty Playwright collection cannot publish a success report', async t => {
  const f = fixture(t, { buyer: "import { test } from '@playwright/test';\nif (false) {\n  test('never collected', () => {});\n}\n" });
  const result = await executeSuite({ suite: 'buyer', env: f.env, projectDirectory: f.projectDirectory });
  assert.equal(result.evidenceValid, false); assert.notEqual(result.exitCode, 0);
  assert.doesNotMatch(readFileSync(f.env.GITHUB_OUTPUT, 'utf8'), /evidence_valid=true|evidence_path=/);
});
