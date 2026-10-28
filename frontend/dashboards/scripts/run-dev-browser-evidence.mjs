import { spawn } from 'node:child_process';
import { Buffer } from 'node:buffer';
import { createRequire } from 'node:module';
import { appendFileSync, chmodSync, lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath, URL } from 'node:url';
import { createContext, PHASES, reject, sha256, SUITES, validateReport } from './browser-evidence-schema.mjs';

const MAX_REPORT_BYTES = 16 * 1024 * 1024;
const HERE = path.dirname(fileURLToPath(import.meta.url));

export function validateCandidate(candidatePath, context) {
  const info = lstatSync(candidatePath);
  if (!info.isFile() || info.isSymbolicLink() || info.size === 0 || info.size > MAX_REPORT_BYTES) reject();
  return validateReport(JSON.parse(readFileSync(candidatePath, 'utf8')), context);
}

function output(env, values) {
  if (!env.GITHUB_OUTPUT) return;
  // All values are fixed enums or parent-generated paths. Reject line breaks
  // instead of letting any environment value add a GitHub output command.
  if (Object.values(values).some(value => /[\r\n]/.test(String(value)))) reject();
  appendFileSync(env.GITHUB_OUTPUT, Object.entries(values).map(([key, value]) => `${key}=${value}\n`).join(''));
}

function runChild(cli, args, env, projectDirectory) {
  return new Promise(resolve => {
    const child = spawn(process.execPath, [cli, ...args], {
      cwd: projectDirectory, env, stdio: ['ignore', 'pipe', 'pipe'],
    });
    // Drain without retaining or printing arbitrary application/Playwright
    // output, including failures before the custom reporter is initialized.
    child.stdout.resume(); child.stderr.resume();
    child.once('error', () => resolve({ exit_code: 1, interrupted: false }));
    child.once('close', (code, signal) => resolve({
      exit_code: Number.isInteger(code) && code >= 0 && code <= 255 ? code : 1,
      interrupted: signal !== null,
    }));
  });
}

export async function executeSuite({ suite, env = process.env, projectDirectory = path.resolve(HERE, '..') }) {
  if (!Object.hasOwn(SUITES, suite)) reject();
  if (typeof env.RUNNER_TEMP !== 'string' || !path.isAbsolute(env.RUNNER_TEMP) || /[\r\n]/.test(env.RUNNER_TEMP)) reject();
  const temporaryRoot = realpathSync(env.RUNNER_TEMP);
  if (!lstatSync(temporaryRoot).isDirectory()) reject();
  const privateRoot = mkdtempSync(path.join(temporaryRoot, 'crown-dev-evidence-'));
  chmodSync(privateRoot, 0o700);
  const publication = path.join(privateRoot, 'publish');
  const reports = [];
  const phases = [];
  let exitCode = 0;
  output(env, { evidence_valid: 'false' });
  try {
    const executionEnv = { ...env };
    if (suite === 'buyer') {
      // Preserve the existing buyer wrapper's URL and headed-mode behavior,
      // without printing its URL or diagnostic output location.
      exitCode = 2;
      const liveUrl = String(env.CROWN_LIVE_FRONTEND_URL || '').trim().replace(/\/$/, '');
      if (!liveUrl) reject();
      const parsed = new URL(liveUrl);
      if (parsed.protocol !== 'https:' && parsed.hostname !== 'localhost') reject();
      executionEnv.CROWN_LIVE_FRONTEND_URL = liveUrl;
      executionEnv.CROWN_BROWSER_AUTHORITY_OUTPUT = env.CROWN_BROWSER_AUTHORITY_OUTPUT || path.resolve(projectDirectory, 'test-results/buyer-sandbox-browser-authority.json');
      exitCode = 0;
    }
    const require = createRequire(path.join(projectDirectory, 'package.json'));
    const cli = path.join(path.dirname(require.resolve('playwright/package.json')), 'cli.js');
    for (const phase of SUITES[suite]) {
      const context = createContext(env, projectDirectory, phase);
      const staging = path.join(privateRoot, phase);
      mkdirSync(staging, { mode: 0o700 });
      const contextPath = path.join(staging, 'context.json');
      const reportPath = path.join(staging, 'candidate.json');
      writeFileSync(contextPath, `${JSON.stringify(context)}\n`, { flag: 'wx', mode: 0o600 });
      const childArgs = [
        'test', PHASES[phase], '--config=playwright.dev-evidence.config.ts', '--workers=1',
      ];
      if (suite === 'buyer' && env.CROWN_DEMO_HEADED === '1') childArgs.push('--headed');
      const child = await runChild(cli, childArgs, {
        ...executionEnv,
        CROWN_CERTIFICATION_LIVE_RUNTIME: '1',
        CROWN_SAFE_EVIDENCE_CONTEXT: contextPath,
        CROWN_SAFE_EVIDENCE_REPORT: reportPath,
        CROWN_SAFE_EVIDENCE_PROJECT: projectDirectory,
        CROWN_SAFE_EVIDENCE_TEST_OUTPUT: path.join(staging, 'unpublished-test-output'),
      }, projectDirectory);
      if (child.exit_code !== 0) exitCode = child.exit_code;
      if (child.interrupted) reject();
      const report = validateCandidate(reportPath, context);
      // A report must agree with the child status. Never turn a failed test
      // command into a passing job because its safe export was valid.
      if ((child.exit_code === 0) !== (report.runner_status === 'passed')) reject();
      reports.push({ phase, report });
      phases.push({ phase, execution: 'completed', runner_exit_code: child.exit_code, runner_status: report.runner_status });
      if (child.exit_code !== 0) {
        exitCode = child.exit_code;
        break; // Preserve the existing preflight && crawler short circuit.
      }
    }
    for (const phase of SUITES[suite].slice(phases.length)) {
      phases.push({ phase, execution: 'not_run_prior_phase_failed' });
    }
    if (reports.length === 0) reject();
    mkdirSync(publication, { mode: 0o700 });
    const files = reports.map(({ phase, report }) => {
      const file = `${phase}.json`;
      const bytes = Buffer.from(`${JSON.stringify(report, null, 2)}\n`);
      writeFileSync(path.join(publication, file), bytes, { flag: 'wx', mode: 0o600 });
      return { path: file, bytes: bytes.length, sha256: sha256(bytes) };
    });
    const context = reports[0].report.context;
    const manifest = {
      schema_version: 1, evidence_kind: 'safe_dev_browser_execution_package',
      repository: context.repository, run_id: context.run_id, run_attempt: context.run_attempt,
      suite, source: context.source, phases, files,
      original_diagnostics_included: false,
      certification_claim: 'not_established_by_this_package',
      limits: [
        'Source locations and collection ordinals identify tests; runtime titles and native test IDs are omitted.',
        'Counts and bounded statuses preserve execution results; raw errors, attachments and application content are omitted.',
        'This report does not replace full diagnostics or establish current operational certification.',
      ],
    };
    writeFileSync(path.join(publication, 'MANIFEST.json'), `${JSON.stringify(manifest, null, 2)}\n`, { flag: 'wx', mode: 0o600 });
    const expected = ['MANIFEST.json', ...files.map(file => file.path)].sort();
    if (JSON.stringify(readdirSync(publication).sort()) !== JSON.stringify(expected)) reject();
    for (const file of files) {
      const bytes = readFileSync(path.join(publication, file.path));
      if (bytes.length !== file.bytes || sha256(bytes) !== file.sha256) reject();
      validateReport(JSON.parse(bytes), reports.find(report => `${report.phase}.json` === file.path).report.context);
    }
    output(env, { evidence_path: publication, evidence_valid: 'true' });
    return { exitCode, evidenceValid: true, evidencePath: publication, manifest };
  } catch {
    rmSync(publication, { recursive: true, force: true });
    output(env, { evidence_valid: 'false' });
    return { exitCode: exitCode || 1, evidenceValid: false };
  } finally {
    for (const phase of SUITES[suite]) rmSync(path.join(privateRoot, phase), { recursive: true, force: true });
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 4 || process.argv[2] !== '--suite') reject();
    const result = await executeSuite({ suite: process.argv[3] });
    process.stdout.write(result.evidenceValid
      ? 'CROWN DEV bounded browser evidence validated.\n'
      : 'CROWN DEV browser evidence rejected; no artifact is eligible for upload.\n');
    process.exitCode = result.exitCode;
  } catch {
    process.stderr.write('CROWN DEV browser evidence could not be initialized.\n');
    process.exitCode = 1;
  }
}
