#!/usr/bin/env node
/**
 * Crown Full Surface Verification Runner
 * Executes each surface gate in sequence; breaks and exits 1 on first failure.
 * Writes a timestamped JSON manifest + raw log to artifacts/verification/.
 */

import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const ARTIFACT_DIR = join(ROOT, "artifacts", "verification");

const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, "-");
const MANIFEST_FILE = join(ARTIFACT_DIR, `verification-manifest-${TIMESTAMP}.json`);
const LOG_FILE = join(ARTIFACT_DIR, `verification-raw-${TIMESTAMP}.log`);
const DEFAULT_GATE_TIMEOUT_MS = Number(process.env.CROWN_VERIFY_GATE_TIMEOUT_MS || 20 * 60 * 1000);

// ── Surface gate command list ──────────────────────────────────────────────
const commands = [
  { label: "lint",                          cmd: "npm run lint" },
  { label: "build",                         cmd: "npm run build" },
  { label: "test:contracts",               cmd: "npm run test:contracts" },
  { label: "check:shell-backend-contract-parity", cmd: "npm run check:shell-backend-contract-parity" },
  { label: "ui:proof:nav",                 cmd: "npm run ui:proof:nav" },
  { label: "ui:proof:matrix-pack-3",       cmd: "npm run ui:proof:matrix-pack-3" },
  { label: "test:release:routes",          cmd: "npm run test:release:routes" },
  { label: "test:release:a11y",            cmd: "npm run test:release:a11y" },
];

// ── Helpers ─────────────────────────────────────────────────────────────────
function log(msg) {
  process.stdout.write(msg + "\n");
  rawLog.push(msg);
}

function runCmd(cmd) {
  const [prog, ...args] = cmd.split(" ");
  const result = spawnSync(prog, args, {
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

// ── Main ─────────────────────────────────────────────────────────────────────
mkdirSync(ARTIFACT_DIR, { recursive: true });

const rawLog = [];
const results = [];
let failed = false;

log(`[crown:verify] CROWN FULL SURFACE VERIFICATION`);
log(`[crown:verify] Started: ${new Date().toISOString()}`);
log(`[crown:verify] Artifact dir: ${ARTIFACT_DIR}`);
log(`[crown:verify] Total gates: ${commands.length}`);
  log(`[crown:verify] Gate timeout: ${DEFAULT_GATE_TIMEOUT_MS}ms`);
log("─".repeat(72));

for (const { label, cmd } of commands) {
  log(`\n[GATE] ${label}`);
  log(`  cmd: ${cmd}`);

  const start = Date.now();
  const { stdout, stderr, status, timedOut } = runCmd(cmd);
  const elapsed = ((Date.now() - start) / 1000).toFixed(1);
  const passed = status === 0;

  if (stdout) stdout.split("\n").forEach((l) => log(`  | ${l}`));
  if (stderr) stderr.split("\n").forEach((l) => log(`  ! ${l}`));
  if (timedOut) log(`  ! command timed out after ${DEFAULT_GATE_TIMEOUT_MS}ms`);

  const outcome = passed ? "PASS" : "FAIL";
  log(`  → ${outcome} (exit ${status}, ${elapsed}s)`);

  results.push({ label, cmd, status, elapsed: `${elapsed}s`, outcome });

  if (!passed) {
    failed = true;
    log(`\n[crown:verify] ABORT: gate "${label}" failed with exit ${status}.`);
    break;
  }
}

log("─".repeat(72));
log(`[crown:verify] Finished: ${new Date().toISOString()}`);

const summary = {
  timestamp: new Date().toISOString(),
  passed: results.filter((r) => r.outcome === "PASS").length,
  failed: results.filter((r) => r.outcome === "FAIL").length,
  total: commands.length,
  overall: failed ? "FAIL" : "PASS",
  gates: results,
};

log(`[crown:verify] Summary: ${summary.passed}/${commands.length} gates PASS — overall: ${summary.overall}`);

writeFileSync(MANIFEST_FILE, JSON.stringify(summary, null, 2), "utf8");
writeFileSync(LOG_FILE, rawLog.join("\n"), "utf8");

log(`[crown:verify] Manifest: ${MANIFEST_FILE}`);
log(`[crown:verify] Log:      ${LOG_FILE}`);

process.exit(failed ? 1 : 0);
