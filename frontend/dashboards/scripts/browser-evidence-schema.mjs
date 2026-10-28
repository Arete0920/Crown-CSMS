import { createHash, randomBytes } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { lstatSync, readFileSync, realpathSync } from 'node:fs';
import path from 'node:path';
import { isDeepStrictEqual } from 'node:util';

export const PHASES = Object.freeze({
  preflight: 'tests/certification/production-runtime-preflight.spec.ts',
  crawler: 'tests/certification/production-certification-crawler.spec.ts',
  buyer: 'tests/certification/buyer-sandbox-browser-authority.spec.ts',
  'tenant-isolation': 'tests/certification/production-tenant-isolation.spec.ts',
});
export const SUITES = Object.freeze({
  certification: ['preflight', 'crawler'],
  buyer: ['buyer'],
  'tenant-isolation': ['tenant-isolation'],
});
export const EXPORTER_FILES = Object.freeze([
  'scripts/browser-evidence-schema.mjs',
  'scripts/dev-browser-evidence-reporter.mjs',
  'scripts/run-dev-browser-evidence.mjs',
  'playwright.dev-evidence.config.ts',
]);
const REPOSITORY = 'Arete0920/Crown-CSMS';
const PREFIX = 'frontend/dashboards/';
const SHA = /^[0-9a-f]{40}$/;
const SHA256 = /^[0-9a-f]{64}$/;
const TEST_STATUSES = new Set(['passed', 'failed', 'skipped', 'timedOut', 'interrupted']);
const RUN_STATUSES = new Set(['passed', 'failed', 'timedout', 'interrupted']);
const OUTCOMES = new Set(['expected', 'unexpected', 'flaky', 'skipped', 'not_run']);
const MAX_COUNT = 100_000;
const MAX_DURATION_MS = 86_400_000;
export const OMITTED = Object.freeze([
  'titles', 'messages', 'stacks', 'annotations', 'stdout', 'stderr',
  'attachments', 'traces', 'har', 'screenshots', 'video', 'storageState',
  'request_response_bodies', 'headers', 'auth_session_material', 'person_school_values',
]);

export function reject() { throw new Error('SAFE_BROWSER_EVIDENCE_INVALID'); }
function check(condition) { if (!condition) reject(); }
function keys(value, expected) {
  check(value && typeof value === 'object' && !Array.isArray(value));
  check(isDeepStrictEqual(Object.keys(value).sort(), [...expected].sort()));
}
function integer(value, maximum = MAX_COUNT) {
  check(Number.isSafeInteger(value) && value >= 0 && value <= maximum);
  return value;
}
function duration(value) {
  check(typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= MAX_DURATION_MS);
  return value;
}
function arrayLength(value) { check(Array.isArray(value)); return integer(value.length); }
function enumeration(value, allowed) { check(allowed.has(value)); return value; }
function isoDate(value) {
  check(value instanceof Date);
  const millis = Date.prototype.getTime.call(value);
  check(Number.isFinite(millis));
  return new Date(millis).toISOString();
}
export function sha256(value) { return createHash('sha256').update(value).digest('hex'); }
function gitBlob(value) {
  return createHash('sha1').update(`blob ${value.length}\0`).update(value).digest('hex');
}
function git(root, args) {
  return execFileSync('git', args, { cwd: root, stdio: ['ignore', 'pipe', 'pipe'], maxBuffer: 8 * 1024 * 1024 });
}

// File names are policy constants. No runtime title, URL, path or error is hashed.
export function createContext(env, projectDirectory, phase) {
  check(Object.hasOwn(PHASES, phase));
  check(env.GITHUB_REPOSITORY === REPOSITORY);
  check(/^[1-9]\d{0,19}$/.test(env.GITHUB_RUN_ID ?? ''));
  check(/^[1-9]\d{0,5}$/.test(env.GITHUB_RUN_ATTEMPT ?? ''));
  const source = {
    runtime_sha: env.CROWN_EVIDENCE_RUNTIME_SHA,
    test_sha: env.CROWN_EVIDENCE_TEST_SHA,
    exporter_sha: env.CROWN_EVIDENCE_EXPORTER_SHA,
  };
  check(Object.values(source).every(value => typeof value === 'string' && SHA.test(value)));
  const root = git(projectDirectory, ['rev-parse', '--show-toplevel']).toString('utf8').trim();
  check(realpathSync(path.join(root, 'frontend/dashboards')) === realpathSync(projectDirectory));
  check(git(root, ['rev-parse', 'HEAD']).toString('utf8').trim() === source.runtime_sha);
  const definitions = [
    ...EXPORTER_FILES.map(relative => [relative, 'exporter', source.exporter_sha]),
    ['playwright.config.ts', 'runtime', source.runtime_sha],
    ['package.json', 'runtime', source.runtime_sha],
    ['package-lock.json', 'runtime', source.runtime_sha],
    [PHASES[phase], 'test', source.test_sha],
  ];
  const files = definitions.map(([relative, role, commit]) => {
    const repositoryPath = PREFIX + relative;
    const absolute = path.join(root, repositoryPath);
    check(lstatSync(absolute).isFile() && !lstatSync(absolute).isSymbolicLink());
    const actual = readFileSync(absolute);
    const committed = git(root, ['show', `${commit}:${repositoryPath}`]);
    check(actual.equals(committed));
    const lines = actual.toString('utf8').split(/\r?\n/);
    return {
      path: repositoryPath, role, source_sha: commit, blob_sha: gitBlob(actual),
      sha256: sha256(actual), bytes: actual.length,
      // A location must refer to a test declaration in the verified source.
      test_locations: role === 'test' ? lines.flatMap((line, index) =>
        [...line.matchAll(/\btest(?:\.(only|skip|fixme))?\s*\(/g)]
          .filter(match => match.index === 0 || line[match.index - 1] !== '.')
          // V8 reports the called property for test.skip/only/fixme, and
          // the test identifier for a direct test(...) call.
          .map(match => ({ line: index + 1, column: match.index + (match[1] ? 6 : 1) }))) : [],
    };
  });
  const context = {
    schema_version: 1, repository: REPOSITORY,
    run_id: env.GITHUB_RUN_ID, run_attempt: Number(env.GITHUB_RUN_ATTEMPT),
    phase, invocation_nonce: randomBytes(32).toString('hex'), source, files,
  };
  validateContext(context);
  return context;
}

export function validateContext(context) {
  keys(context, ['schema_version', 'repository', 'run_id', 'run_attempt', 'phase', 'invocation_nonce', 'source', 'files']);
  check(context.schema_version === 1 && context.repository === REPOSITORY);
  check(typeof context.run_id === 'string' && /^[1-9]\d{0,19}$/.test(context.run_id));
  check(integer(context.run_attempt, 999_999) > 0 && Object.hasOwn(PHASES, context.phase));
  check(typeof context.invocation_nonce === 'string' && SHA256.test(context.invocation_nonce));
  keys(context.source, ['runtime_sha', 'test_sha', 'exporter_sha']);
  check(Object.values(context.source).every(value => typeof value === 'string' && SHA.test(value)));
  const expected = new Map([
    ...EXPORTER_FILES.map(file => [PREFIX + file, 'exporter']),
    ...['playwright.config.ts', 'package.json', 'package-lock.json'].map(file => [PREFIX + file, 'runtime']),
    [PREFIX + PHASES[context.phase], 'test'],
  ]);
  check(Array.isArray(context.files) && context.files.length === expected.size);
  const seen = new Set();
  for (const file of context.files) {
    keys(file, ['path', 'role', 'source_sha', 'blob_sha', 'sha256', 'bytes', 'test_locations']);
    check(expected.get(file.path) === file.role && !seen.has(file.path)); seen.add(file.path);
    check(file.source_sha === context.source[`${file.role}_sha`]);
    check(typeof file.blob_sha === 'string' && SHA.test(file.blob_sha));
    check(typeof file.sha256 === 'string' && SHA256.test(file.sha256)); integer(file.bytes, 8 * 1024 * 1024);
    check(Array.isArray(file.test_locations));
    if (file.role !== 'test') check(file.test_locations.length === 0);
    for (const location of file.test_locations) {
      keys(location, ['line', 'column']);
      check(integer(location.line) > 0 && integer(location.column) > 0);
    }
    if (file.role === 'test') check(file.test_locations.length > 0);
  }
  return context;
}

function testSource(context) { return context.files.find(file => file.role === 'test'); }
function locationId(phase, line, column, ordinal) { return `${phase}:${line}:${column}:${ordinal}`; }
function sourceLocation(context, location, projectDirectory) {
  const source = testSource(context);
  check(location && typeof location.file === 'string');
  check(path.resolve(location.file) === path.resolve(projectDirectory, PHASES[context.phase]));
  const line = integer(location.line); const column = integer(location.column);
  check(column > 0 && source.test_locations.some(item => item.line === line && column === item.column));
  return { path: source.path, blob_sha: source.blob_sha, line, column };
}

function observeResult(result) {
  return {
    retry: integer(result.retry, 100),
    status: enumeration(result.status, TEST_STATUSES), duration_ms: duration(result.duration),
    error_count: arrayLength(result.errors),
    omitted_attachment_count: arrayLength(result.attachments),
    omitted_stdout_chunk_count: arrayLength(result.stdout), omitted_stderr_chunk_count: arrayLength(result.stderr),
  };
}

function consistentOutcome(record) {
  if (record.results.length === 0) return 'not_run';
  // Playwright's outcome distinguishes an expected failure from a failed
  // assertion. Skipped/interrupted observations are not completed assertions.
  const completed = record.results.filter(result => !['skipped', 'interrupted'].includes(result.status));
  const expected = completed.some(result => result.status === record.expected_status);
  const unexpected = completed.some(result => result.status !== record.expected_status);
  if (!expected && !unexpected) return 'skipped';
  if (!unexpected) return 'expected';
  const expectedSkip = record.expected_status === 'skipped' && record.results.some(result => result.status === 'skipped');
  return expected || expectedSkip ? 'flaky' : 'unexpected';
}

export class EvidenceCollector {
  constructor(context, projectDirectory) {
    this.context = validateContext(context); this.projectDirectory = projectDirectory;
    this.cases = []; this.references = new Map(); this.globalErrors = 0; this.invalid = false;
  }
  guard(callback) { try { callback(); } catch { this.invalid = true; } }
  begin(tests) {
    check(this.cases.length === 0 && Array.isArray(tests) && tests.length > 0 && tests.length <= MAX_COUNT);
    const ordinals = new Map();
    for (const test of tests) {
      const source = sourceLocation(this.context, test.location, this.projectDirectory);
      const key = `${source.line}:${source.column}`;
      const ordinal = (ordinals.get(key) ?? 0) + 1; ordinals.set(key, ordinal);
      check(!this.references.has(test));
      const record = {
        case_id: locationId(this.context.phase, source.line, source.column, ordinal),
        source, ordinal, expected_status: enumeration(test.expectedStatus, new Set(['passed', 'failed', 'skipped'])),
        outcome: 'not_run', results: [],
      };
      this.references.set(test, record); this.cases.push(record);
    }
  }
  endTest(test, result) {
    const record = this.references.get(test); check(record);
    record.expected_status = enumeration(test.expectedStatus, new Set(['passed', 'failed', 'skipped']));
    const observation = observeResult(result);
    check(!record.results.some(item => item.retry === observation.retry)); record.results.push(observation);
  }
  error() { this.globalErrors += 1; if (this.globalErrors > MAX_COUNT) this.invalid = true; }
  finish(result) {
    check(!this.invalid);
    for (const [test, record] of this.references) {
      record.expected_status = enumeration(test.expectedStatus, new Set(['passed', 'failed', 'skipped']));
      // Reconcile with Playwright's final API collection. A missing retry
      // callback must not yield a partial report that appears successful.
      check(Array.isArray(test.results) && test.results.length <= 101);
      check(isDeepStrictEqual(test.results.map(observeResult), record.results));
      if (record.results.length) record.outcome = enumeration(test.outcome(), OUTCOMES);
    }
    const report = {
      schema_version: 1, evidence_kind: 'bounded_dev_browser_execution', context: this.context,
      runner_status: enumeration(result.status, RUN_STATUSES), started_at_utc: isoDate(result.startTime),
      duration_ms: duration(result.duration), global_error_count: integer(this.globalErrors),
      cases: this.cases, omitted: [...OMITTED],
      certification_claim: 'not_established_by_this_report',
    };
    validateReport(report, this.context);
    return report;
  }
}

export function validateReport(report, expectedContext) {
  validateContext(expectedContext);
  keys(report, ['schema_version', 'evidence_kind', 'context', 'runner_status', 'started_at_utc', 'duration_ms', 'global_error_count', 'cases', 'omitted', 'certification_claim']);
  check(report.schema_version === 1 && report.evidence_kind === 'bounded_dev_browser_execution');
  check(isDeepStrictEqual(report.context, expectedContext));
  enumeration(report.runner_status, RUN_STATUSES); duration(report.duration_ms); integer(report.global_error_count);
  check(typeof report.started_at_utc === 'string' && /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(report.started_at_utc));
  check(Number.isFinite(Date.parse(report.started_at_utc)) && new Date(report.started_at_utc).toISOString() === report.started_at_utc);
  check(isDeepStrictEqual(report.omitted, OMITTED) && report.certification_claim === 'not_established_by_this_report');
  check(Array.isArray(report.cases) && report.cases.length <= MAX_COUNT);
  const source = testSource(expectedContext); const ids = new Set(); const ordinals = new Map();
  for (const record of report.cases) {
    keys(record, ['case_id', 'source', 'ordinal', 'expected_status', 'outcome', 'results']);
    keys(record.source, ['path', 'blob_sha', 'line', 'column']);
    check(record.source.path === source.path && record.source.blob_sha === source.blob_sha);
    check(integer(record.source.line) > 0 && integer(record.source.column) > 0 && source.test_locations.some(item => item.line === record.source.line && record.source.column === item.column));
    const locationKey = `${record.source.line}:${record.source.column}`;
    const ordinal = (ordinals.get(locationKey) ?? 0) + 1; ordinals.set(locationKey, ordinal);
    check(record.ordinal === ordinal);
    check(record.case_id === locationId(expectedContext.phase, record.source.line, record.source.column, ordinal) && !ids.has(record.case_id)); ids.add(record.case_id);
    enumeration(record.expected_status, new Set(['passed', 'failed', 'skipped'])); enumeration(record.outcome, OUTCOMES);
    check(Array.isArray(record.results) && record.results.length <= 101);
    const retries = new Set();
    for (const result of record.results) {
      keys(result, ['retry', 'status', 'duration_ms', 'error_count', 'omitted_attachment_count', 'omitted_stdout_chunk_count', 'omitted_stderr_chunk_count']);
      integer(result.retry, 100); check(!retries.has(result.retry)); retries.add(result.retry);
      enumeration(result.status, TEST_STATUSES); duration(result.duration_ms);
      for (const field of ['error_count', 'omitted_attachment_count', 'omitted_stdout_chunk_count', 'omitted_stderr_chunk_count']) integer(result[field]);
    }
    check(record.results.length > 0 ? record.outcome !== 'not_run' : record.outcome === 'not_run');
    check(record.outcome === consistentOutcome(record));
  }
  // List-only, interrupted collection, missing callbacks and swallowed callback
  // errors must never produce a valid successful-execution report.
  if (report.runner_status === 'passed') {
    check(report.cases.length > 0 && report.global_error_count === 0);
    check(report.cases.every(record => record.results.length > 0 && ['expected', 'flaky', 'skipped'].includes(record.outcome)));
  }
  return report;
}
