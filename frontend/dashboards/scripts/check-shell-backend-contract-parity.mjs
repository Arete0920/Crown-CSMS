/* global console, process */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CONTRACT_PATH = path.resolve(__dirname, "../../../contracts/shell_backend_contract.json");

function fail(message) {
  console.error(message);
  process.exit(1);
}

if (!fs.existsSync(CONTRACT_PATH)) {
  fail(`Canonical contract file not found: ${CONTRACT_PATH}`);
}

const canonical = JSON.parse(fs.readFileSync(CONTRACT_PATH, "utf8"));
const wizards = Array.isArray(canonical.wizards) ? canonical.wizards : [];
const dashboardModules = Array.isArray(canonical.dashboardModules) ? canonical.dashboardModules : [];

if (canonical.version !== 5) {
  fail(`Expected canonical contract version 5, found ${canonical.version}`);
}

if (wizards.length === 0) {
  fail("Canonical contract has no wizard entries.");
}

const requiredWizardFields = [
  "moduleKey",
  "path",
  "apiPrefix",
  "requiresAuth",
  "requiresSchoolHeader",
  "schoolHeaderName",
  "probeSchoolId",
  "acceptableUnauthenticatedStatusCodes",
  "acceptableMissingSchoolHeaderStatusCodes",
  "acceptableAuthenticatedStatusCodes",
  "requiresSeededSuccess",
  "seededSuccessProbeMethod",
  "acceptableSeededSuccessStatusCodes",
  "requiresWriteProof",
  "writeProbeMethod",
  "acceptableWriteStatusCodes",
  "expectedWriteJsonTopLevelKinds",
  "requiresLifecycleReadBackProof",
  "readBackProbeMethod",
  "acceptableReadBackStatusCodes",
  "expectedReadBackJsonTopLevelKinds",
  "expectedJsonTopLevelKinds",
];

const moduleKeys = new Set();
const apiPrefixes = new Set();

for (const row of wizards) {
  for (const field of requiredWizardFields) {
    if (!(field in row)) {
      fail(`Wizard entry missing required field '${field}': ${JSON.stringify(row)}`);
    }
  }

  if (moduleKeys.has(row.moduleKey)) {
    fail(`Duplicate moduleKey in canonical contract: ${row.moduleKey}`);
  }
  moduleKeys.add(row.moduleKey);

  if (apiPrefixes.has(row.apiPrefix)) {
    fail(`Duplicate apiPrefix in canonical contract: ${row.apiPrefix}`);
  }
  apiPrefixes.add(row.apiPrefix);
}

console.log(
  `PASS: shell backend contract validated (version=${canonical.version}, wizards=${wizards.length}, dashboardModules=${dashboardModules.length}).`
);
