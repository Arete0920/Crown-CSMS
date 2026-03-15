/* eslint-env node */
/* global console, process */

import {
  getFakeReadyRoutes,
  getModuleReadinessSummary,
} from "../src/config/moduleReadiness.js";

const summary = getModuleReadinessSummary();
const findings = getFakeReadyRoutes();

console.log("=== MODULE READINESS SUMMARY ===");
console.log(JSON.stringify(summary, null, 2));

if (findings.length > 0) {
  console.log("");
  console.log("=== FAKE READY ROUTES ===");
  console.log(
    JSON.stringify(
      findings.map((finding) => ({
        type: finding.type,
        field: finding.field || null,
        flag: finding.flag || null,
        moduleKey: finding.entry?.moduleKey || null,
        moduleType: finding.entry?.moduleType || finding.entry?.__moduleType || null,
        path: finding.entry?.path || finding.entry?.__path || null,
        source: finding.entry?.__source || null,
        componentName: finding.entry?.__componentName || null,
        releaseState: finding.entry?.releaseState || finding.entry?.__releaseState || null,
      })),
      null,
      2
    )
  );
  process.exitCode = 1;
} else {
  console.log("");
  console.log("No fake ready routes found.");
}
