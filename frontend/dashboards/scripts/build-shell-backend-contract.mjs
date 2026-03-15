/* eslint-env node */
/* global console */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const CONTRACT_PATH = path.resolve(__dirname, "../../../contracts/shell_backend_contract.json");

const canonical = JSON.parse(fs.readFileSync(CONTRACT_PATH, "utf8"));

console.log(
  JSON.stringify(
    {
      version: canonical.version,
      wizards: canonical.wizards || [],
      dashboardModules: canonical.dashboardModules || [],
    },
    null,
    2
  )
);
