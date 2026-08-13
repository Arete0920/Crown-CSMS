#!/usr/bin/env node
/**
 * Crown Full Surface Verification Runner
 * Executes each surface gate in sequence; breaks and exits 1 on first failure.
 * Writes timestamped evidence plus stable latest/failure files for CI diagnosis.
 */

import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const ARTIFACT_DIR = join(ROOT, "artifacts", "verification");

function positiveIntegerEnv(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === "") return fallback;
  const parsed = Number(raw);
  if (!Number.isSafeInteger(parsed) || parsed <= 0) {
    throw new Error(`${name} must be a positive integer; received ${JSON.stringify(raw)}.`);
  }
  return parsed;
}

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, "-");
const MANIFEST_FILE = join(ARTIFACT_DIR, `verification-manifest-${TIMESTAMP}.json`);
const LOG_FILE = join(ARTIFACT_DIR, `verification-raw-${TIMESTAMP}.log`);
const LATEST_MANIFEST_FILE = join(ARTIFACT_DIR, "verification-latest.json");
const LATEST_LOG_FILE = join(ARTIFACT_DIR, "verification-latest.log");
const FAILURE_FILE = join(ARTIFACT_DIR, "verification-failure.log");
const DEFAULT_GATE_TIMEOUT_MS = positiveIntegerEnv("CROWN_VERIFY_GATE_TIMEOUT_MS", 20 * 60 * 1000);
const FAILURE_TAIL_LINES = positiveIntegerEnv("CROWN_VERIFY_FAILURE_TAIL_LINES", 120);

const commands = [
  { label: "lint", cmd: "npm run lint" },
  { label: "build", cmd: "npm run build" },
  { label: "check:visual-system", cmd: "npm run check:visual-system" },
  { label: "test:contracts", cmd: "npm run test:contracts" },
  { label: "check:shell-certification", cmd: "npm run check:shell-certification" },
  { label: "check:shell-backend-contract-parity", cmd: "npm run check:shell-backend-contract-parity" },
  { label: "verify:dashboard-completeness", cmd: "npm run verify:dashboard-completeness" },
  { label: "ui:proof:nav", cmd: "npm run ui:proof:nav" },
  { label: "ui:proof:nav-perms", cmd: "npm run ui:proof:nav-perms" },
  { label: "ui:proof:matrix", cmd: "npm run ui:proof:matrix" },
  { label: "ui:proof:matrix-pack-2", cmd: "npm run ui:proof:matrix-pack-2" },
  { label: "ui:proof:matrix-pack-3", cmd: "npm run ui:proof:matrix-pack-3" },
  { label: "test:release:routes", cmd: "npm run test:release:routes" },
  { label: "test:release:a11y", cmd: "npm run test:release:a11y" },
  { label: "certify:scaffold-crawler", cmd: "npm run certify:scaffold-crawler" },
];

function consoleLog(message) {
  process.stdout.write(`${message}\n`);
}

function appendRaw(message) {
  rawLog.push(message);
}

function record(message) {
  consoleLog(message);
  appendRaw(message);
}

function runCmd(cmd) {
  const [program, ...args] = cmd.split(" ");
  const result = spawnSync(program, args, {
    cwd: ROOT,
    shell: true,
    encoding: "utf8",
    stdio: ["inherit", "pipe", "pipe"],
    timeout: DEFAULT_GATE_TIMEOUT_MS,
  });
  return {
    stdout: result.stdout || "",
    stderr: result.stderr || "",
    status: result.status ?? 1,
    timedOut: Boolean(result.error && result.error.code === "ETIMEDOUT"),
  };
}

function outputLines(stdout, stderr) {
  return [
    ...stdout.split("\n").filter(Boolean).map((line) => `stdout | ${line}`),
    ...stderr.split("\n").filter(Boolean).map((line) => `stderr | ${line}`),
  ];
}

function failureTail(lines) {
  return lines.slice(-FAILURE_TAIL_LINES).join("\n");
}

mkdirSync(ARTIFACT_DIR, { recursive: true });

const rawLog = [];
const results = [];
let failed = false;
let failureEvidence = "";

record("[crown:verify] CROWN FULL SURFACE VERIFICATION");
record(`[crown:verify] Started: ${new Date().toISOString()}`);
record(`[crown:verify] Artifact dir: ${ARTIFACT_DIR}`);
record(`[crown:verify] Total gates: ${commands.length}`);
record(`[crown:verify] Gate timeout: ${DEFAULT_GATE_TIMEOUT_MS}ms`);
record("-".repeat(72));

for (const { label, cmd } of commands) {
  record(`\n[GATE] ${label}`);
  record(`  cmd: ${cmd}`);

  const start = Date.now();
  const { stdout, stderr, status, timedOut } = runCmd(cmd);
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  const passed = status === 0;
  const lines = outputLines(stdout, stderr);

  for (const line of lines) appendRaw(`  ${line}`);
  if (timedOut) appendRaw(`  command timed out after ${DEFAULT_GATE_TIMEOUT_MS}ms`);

  const outcome = passed ? "PASS" : "FAIL";
  record(`  -> ${outcome} (exit ${status}, ${elapsed}s)`);

  results.push({ label, cmd, status, elapsed: `${elapsed}s`, outcome, timedOut });

  if (!passed) {
    failed = true;
    const tail = failureTail(lines);
    failureEvidence = [
      `gate=${label}`,
      `command=${cmd}`,
      `exit=${status}`,
      `timed_out=${timedOut}`,
      `elapsed=${elapsed}s`,
      "",
      tail || "(command produced no stdout/stderr)",
      "",
    ].join("\n");

    consoleLog(`::error title=CROWN full verification failed::Gate ${label} failed with exit ${status}`);
    consoleLog("[crown:verify] ACTIONABLE FAILURE TAIL");
    consoleLog(failureEvidence);
    appendRaw("[crown:verify] ACTIONABLE FAILURE TAIL");
    appendRaw(failureEvidence);
    record(`[crown:verify] ABORT: gate "${label}" failed with exit ${status}.`);
    break;
  }
}

record("-".repeat(72));
record(`[crown:verify] Finished: ${new Date().toISOString()}`);

const summary = {
  timestamp: new Date().toISOString(),
  passed: results.filter((result) => result.outcome === "PASS").length,
  failed: results.filter((result) => result.outcome === "FAIL").length,
  total: commands.length,
  completed: results.length,
  overall: failed ? "FAIL" : "PASS",
  failed_gate: results.find((result) => result.outcome === "FAIL")?.label ?? null,
  gates: results,
};

record(`[crown:verify] Summary: ${summary.passed}/${commands.length} gates PASS - overall: ${summary.overall}`);

const manifestJson = `${JSON.stringify(summary, null, 2)}\n`;
const rawLogText = `${rawLog.join("\n")}\n`;
writeFileSync(MANIFEST_FILE, manifestJson, "utf8");
writeFileSync(LOG_FILE, rawLogText, "utf8");
writeFileSync(LATEST_MANIFEST_FILE, manifestJson, "utf8");
writeFileSync(LATEST_LOG_FILE, rawLogText, "utf8");
writeFileSync(FAILURE_FILE, failureEvidence || "No failure. Full verification passed.\n", "utf8");

consoleLog(`[crown:verify] Manifest: ${MANIFEST_FILE}`);
consoleLog(`[crown:verify] Log: ${LOG_FILE}`);
consoleLog(`[crown:verify] Latest manifest: ${LATEST_MANIFEST_FILE}`);
consoleLog(`[crown:verify] Failure evidence: ${FAILURE_FILE}`);

process.exit(failed ? 1 : 0);
