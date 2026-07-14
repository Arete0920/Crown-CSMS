#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const dashboardRoot = resolve(scriptDir, "..");
const npx = process.platform === "win32" ? "npx.cmd" : "npx";
const result = spawnSync(
  npx,
  [
    "playwright",
    "test",
    "tests/certification/scaffold-certification-crawler.spec.ts",
    "--workers=1",
    "--reporter=line",
  ],
  {
    cwd: dashboardRoot,
    env: process.env,
    encoding: "utf8",
    stdio: "inherit",
  },
);

const evidenceRoot = resolve(
  dashboardRoot,
  "../../audit-artifacts/production-certification/current",
);

const files = [
  "certification-summary.md",
  "route-results.csv",
  "certification-matrix.json",
  "failed-requests.json",
  "console-errors.json",
  "missing-provenance.json",
  "non-live-provenance.json",
  "accessibility-violations.json",
];

process.stdout.write("\n=== SCAFFOLD CERTIFICATION DIAGNOSTICS ===\n");
for (const name of files) {
  const path = resolve(evidenceRoot, name);
  process.stdout.write(`\n--- ${name} ---\n`);
  if (!existsSync(path)) {
    process.stdout.write("(missing)\n");
    continue;
  }
  const contents = readFileSync(path, "utf8");
  process.stdout.write(contents);
  if (!contents.endsWith("\n")) {
    process.stdout.write("\n");
  }
}
process.stdout.write("=== END SCAFFOLD CERTIFICATION DIAGNOSTICS ===\n");

if (result.error) {
  process.stderr.write(`Failed to start scaffold certification crawler: ${result.error.message}\n`);
  process.exit(1);
}

process.exit(result.status ?? 1);
