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

const wizardModuleKeys = new Set();
const apiPrefixes = new Set();

for (const row of wizards) {
  for (const field of requiredWizardFields) {
    if (!(field in row)) {
      fail(`Wizard entry missing required field '${field}': ${JSON.stringify(row)}`);
    }
  }

  if (wizardModuleKeys.has(row.moduleKey)) {
    fail(`Duplicate wizard moduleKey in canonical contract: ${row.moduleKey}`);
  }
  wizardModuleKeys.add(row.moduleKey);

  if (apiPrefixes.has(row.apiPrefix)) {
    fail(`Duplicate apiPrefix in canonical contract: ${row.apiPrefix}`);
  }
  apiPrefixes.add(row.apiPrefix);
}

const requiredDashboardFields = ["moduleKey", "path", "apiContractKey"];
const dashboardModuleKeys = new Set();
const dashboardPaths = new Set();
const dashboardApiContractKeys = new Set();

for (const row of dashboardModules) {
  for (const field of requiredDashboardFields) {
    if (!(field in row) || !String(row[field] || "").trim()) {
      fail(`Dashboard module entry missing required field '${field}': ${JSON.stringify(row)}`);
    }
  }

  if (dashboardModuleKeys.has(row.moduleKey)) {
    fail(`Duplicate dashboard moduleKey in canonical contract: ${row.moduleKey}`);
  }
  dashboardModuleKeys.add(row.moduleKey);

  if (dashboardPaths.has(row.path)) {
    fail(`Duplicate dashboard path in canonical contract: ${row.path}`);
  }
  dashboardPaths.add(row.path);

  if (dashboardApiContractKeys.has(row.apiContractKey)) {
    fail(`Duplicate dashboard apiContractKey in canonical contract: ${row.apiContractKey}`);
  }
  dashboardApiContractKeys.add(row.apiContractKey);
}

console.log(
  `PASS: shell backend contract validated (version=${canonical.version}, wizards=${wizards.length}, dashboardModules=${dashboardModules.length}).`
);
