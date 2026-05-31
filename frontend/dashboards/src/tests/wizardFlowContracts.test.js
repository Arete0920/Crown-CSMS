import { describe, expect, it } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const apiDir = path.resolve(__dirname, '../api');

function getWizardApiFiles() {
  return readdirSync(apiDir)
    .filter((name) => name.endsWith('_wizard.js'))
    .sort();
}

function loadWizardSource(fileName) {
  const filePath = path.resolve(apiDir, fileName);
  return readFileSync(filePath, 'utf8');
}

const wizardFiles = getWizardApiFiles();

const STEP_MUTATOR_PATTERN = /(configure|save|load|stage|define|draft|add|link|preview)/i;

describe('wizard flow contracts', () => {
  it('057: enforces step-completion operation contracts per wizard api module', () => {
    expect(wizardFiles.length).toBeGreaterThan(0);

    wizardFiles.forEach((fileName) => {
      const source = loadWizardSource(fileName);
      const exportedFns = [...source.matchAll(/^export\s+async\s+function\s+([A-Za-z0-9_]+)\s*\(/gm)].map((m) => m[1]);
      const hasStepMutator = exportedFns.some((fnName) => STEP_MUTATOR_PATTERN.test(fnName));
      expect(hasStepMutator, `${fileName} must expose a step-mutating operation`).toBe(true);
    });
  });

  it('058: enforces save-resume continuity per wizard api module', () => {
    wizardFiles.forEach((fileName) => {
      const source = loadWizardSource(fileName);

      const hasCreateSession = /export\s+async\s+function\s+create[A-Za-z0-9_]*Session\s*\(/m.test(source);
      expect(hasCreateSession, `${fileName} must expose create*Session`).toBe(true);

      const sessionArgOccurrences = source.match(/\(\s*sessionId\s*[,)]/g) || [];
      expect(
        sessionArgOccurrences.length,
        `${fileName} must pass sessionId through subsequent flow operations`,
      ).toBeGreaterThanOrEqual(3);

      expect(/\/sessions\/?/.test(source), `${fileName} must target wizard session routes`).toBe(true);
    });
  });

  it('059: enforces commit/apply side-effect contract per wizard api module', () => {
    wizardFiles.forEach((fileName) => {
      const source = loadWizardSource(fileName);

      const hasCommitFn = /export\s+async\s+function\s+commit[A-Za-z0-9_]*\s*\(/m.test(source);
      expect(hasCommitFn, `${fileName} must expose commit operation`).toBe(true);
      expect(source.includes('/commit/'), `${fileName} must call commit endpoint`).toBe(true);
    });
  });

  it('060: enforces downstream reflection check contract per wizard api module', () => {
    wizardFiles.forEach((fileName) => {
      const source = loadWizardSource(fileName);

      const hasVerifyFn = /export\s+async\s+function\s+verify[A-Za-z0-9_]*\s*\(/m.test(source);
      expect(hasVerifyFn, `${fileName} must expose verify operation`).toBe(true);
      expect(source.includes('/verify/'), `${fileName} must call verify endpoint`).toBe(true);
    });
  });
});
