import { describe, expect, it } from 'vitest';
import { readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { WIZARD_MANIFEST } from '../routes/wizard-manifest';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const apiDir = path.resolve(__dirname, '../api');

function apiFileNameForSlug(slug) {
  const normalized = slug.replaceAll('-', '_');
  const wizardBase = normalized.endsWith('_wizard')
    ? normalized
    : `${normalized}_wizard`;
  return `${wizardBase}.js`;
}

describe('wizard manifest api coverage', () => {
  it('requires every manifest wizard to have a matching api module', () => {
    const apiFiles = new Set(
      readdirSync(apiDir).filter((name) => name.endsWith('_wizard.js')),
    );

    const missing = WIZARD_MANIFEST
      .map((wizard) => ({
        slug: wizard.slug,
        expectedFile: apiFileNameForSlug(wizard.slug),
      }))
      .filter((row) => !apiFiles.has(row.expectedFile));

    expect(missing).toEqual([]);
  });
});
