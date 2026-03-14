/* eslint-env node */
/* global console */

import { fileURLToPath } from "node:url";
import { WIZARD_MANIFEST } from "../src/routes/wizard-manifest.js";

export function getFrontendWizardContractRows() {
  return WIZARD_MANIFEST.map((wizard) => ({
    slug: wizard.slug,
    title: wizard.title,
    frontendPath: wizard.path,
  })).sort((a, b) => a.slug.localeCompare(b.slug));
}

const payload = {
  scope: "wizard_registry_parity",
  wizardCount: getFrontendWizardContractRows().length,
  wizards: getFrontendWizardContractRows(),
};

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  console.log(JSON.stringify(payload, null, 2));
}
