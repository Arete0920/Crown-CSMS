import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { WIZARD_MANIFEST } from '../routes/wizard-manifest';
import { WIZARD_REGISTRY } from '../routes/wizards';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const apiDir = path.resolve(__dirname, '../api');

function getWizardApiFiles() {
  return readdirSync(apiDir)
    .filter((name) => name.endsWith('_wizard.js'))
    .sort();
}

function loadWizardSource(fileName) {
  return readFileSync(path.resolve(apiDir, fileName), 'utf8');
}

const wizardApiFiles = getWizardApiFiles();

describe('wizard resilience contracts', () => {
  it('061: enforces rollback/error-recovery surface for critical wizard api flows', () => {
    wizardApiFiles.forEach((fileName) => {
      const source = loadWizardSource(fileName);

      // Any flow that talks to network must expose a deterministic error surface:
      // explicit throw path or delegated canonical clients that normalize errors.
      const hasExplicitThrow = /throw\s+err|throw\s+new\s+Error/.test(source);
      const usesCanonicalClient = /apiFetch\(|crownApiClient\.request\(/.test(source);
      expect(hasExplicitThrow || usesCanonicalClient, `${fileName} must expose recoverable error behavior`).toBe(true);

      // If raw fetch is used directly, non-2xx handling must be explicit.
      if (/globalThis\.fetch\(/.test(source)) {
        expect(/!res\.ok/.test(source), `${fileName} must explicitly guard non-2xx responses`).toBe(true);
      }
    });
  });

  it('062: enforces tenant-isolated wizard surface per manifest slug', () => {
    const routeByPath = new Map(WIZARD_REGISTRY.map((route) => [route.path, route]));

    WIZARD_MANIFEST.forEach((wizard) => {
      const route = routeByPath.get(wizard.path);
      expect(route, `missing wizard route for slug ${wizard.slug}`).toBeTruthy();
      expect(typeof route.apiPrefix).toBe('string');
      expect(route.apiPrefix.startsWith('/api/')).toBe(true);
      expect(route.apiPrefix.includes('/v1/')).toBe(true);
    });

    wizardApiFiles.forEach((fileName) => {
      const source = loadWizardSource(fileName);
      const hasTenantHeader = source.includes('X-School-Id');
      const usesScopedClient = /apiFetch\(|crownApiClient\.request\(/.test(source);
      expect(hasTenantHeader || usesScopedClient, `${fileName} must preserve tenant scoping`).toBe(true);
    });
  });

  it('063: enforces role-access contract per wizard slug', () => {
    const routeByPath = new Map(WIZARD_REGISTRY.map((route) => [route.path, route]));

    WIZARD_MANIFEST.forEach((wizard) => {
      const route = routeByPath.get(wizard.path);
      expect(route, `missing wizard route for slug ${wizard.slug}`).toBeTruthy();
      expect(Array.isArray(route.roles), `roles missing for ${wizard.slug}`).toBe(true);
      expect(route.roles.length, `roles empty for ${wizard.slug}`).toBeGreaterThan(0);
      route.roles.forEach((role) => {
        expect(typeof role).toBe('string');
        expect(role.trim().length).toBeGreaterThan(0);
      });
    });
  });
});
