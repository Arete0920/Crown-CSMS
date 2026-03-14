/* eslint-env node */
/* global console, process */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { getFrontendWizardContractRows } from "./build-shell-backend-contract.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CONTRACT_PATH = path.resolve(__dirname, "../../../contracts/shell_backend_contract.json");

function fail(message) {
  console.error(message);
  process.exit(1);
}

function stableRows(rows) {
  return rows
    .map((row) => ({
      slug: row.slug,
      title: row.title,
      frontendPath: row.frontendPath,
    }))
    .sort((a, b) => a.slug.localeCompare(b.slug));
}

if (!fs.existsSync(CONTRACT_PATH)) {
  fail(`Canonical contract file not found: ${CONTRACT_PATH}`);
}

const canonical = JSON.parse(fs.readFileSync(CONTRACT_PATH, "utf8"));
const canonicalRows = stableRows(canonical.wizards || []);
const frontendRows = stableRows(getFrontendWizardContractRows());

const canonicalSlugs = new Set(canonicalRows.map((row) => row.slug));
const frontendSlugs = new Set(frontendRows.map((row) => row.slug));
const missingFromCanonical = frontendRows.filter((row) => !canonicalSlugs.has(row.slug)).map((row) => row.slug);
const missingFromFrontend = canonicalRows.filter((row) => !frontendSlugs.has(row.slug)).map((row) => row.slug);

if (missingFromCanonical.length > 0) {
  fail(`Canonical contract missing frontend slugs: ${missingFromCanonical.join(", ")}`);
}

if (missingFromFrontend.length > 0) {
  fail(`Frontend wizard manifest missing canonical slugs: ${missingFromFrontend.join(", ")}`);
}

const mismatchedRows = [];
for (const canonicalRow of canonicalRows) {
  const frontendRow = frontendRows.find((row) => row.slug === canonicalRow.slug);
  if (!frontendRow) {
    continue;
  }

  if (frontendRow.title !== canonicalRow.title || frontendRow.frontendPath !== canonicalRow.frontendPath) {
    mismatchedRows.push({
      slug: canonicalRow.slug,
      canonical: canonicalRow,
      frontend: frontendRow,
    });
  }
}

if (mismatchedRows.length > 0) {
  console.error("Canonical/frontend mismatch detected:");
  console.error(JSON.stringify(mismatchedRows, null, 2));
  process.exit(1);
}

const duplicateSlugs = frontendRows
  .map((row) => row.slug)
  .filter((slug, index, list) => list.indexOf(slug) !== index);

if (duplicateSlugs.length > 0) {
  fail(`Duplicate slugs in frontend wizard contract: ${duplicateSlugs.join(", ")}`);
}

console.log(`PASS: frontend contract parity verified (${frontendRows.length} wizard entries).`);
