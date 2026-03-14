/* eslint-env node */
/* global console */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { getFrontendWizardContractRows } from "./build-shell-backend-contract.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CONTRACT_PATH = path.resolve(__dirname, "../../../contracts/shell_backend_contract.json");

const canonical = JSON.parse(fs.readFileSync(CONTRACT_PATH, "utf8"));

console.log("=== CANONICAL CONTRACT (frontend slice) ===");
console.log(
  JSON.stringify(
    (canonical.wizards || [])
      .map((row) => ({
        slug: row.slug,
        title: row.title,
        frontendPath: row.frontendPath,
      }))
      .sort((a, b) => a.slug.localeCompare(b.slug)),
    null,
    2
  )
);

console.log("\n=== FRONTEND DECLARATION ===");
console.log(JSON.stringify(getFrontendWizardContractRows(), null, 2));
