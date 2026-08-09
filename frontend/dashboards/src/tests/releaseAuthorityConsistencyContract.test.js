import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '../../../../');

function readRepoFile(relativePath) {
  const fullPath = path.resolve(repoRoot, relativePath);
  return readFileSync(fullPath, 'utf8');
}

describe('release authority consistency contract', () => {
  it('keeps historical certification distinct from the current owner-handoff decision', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Current handoff decision: **NO-GO / REMEDIATION AND FRESH EXACT-IDENTITY CERTIFICATION REQUIRED**')).toBe(true);
    expect(source.includes('Prior bounded production deployment: **HISTORICAL PASS**')).toBe(true);
    expect(source.includes('Prior Heritage surface matrix: **18/18 HISTORICAL RESULT; NOT CURRENT HANDOFF PROOF**')).toBe(true);
    expect(source.includes('Current buyer diligence package: **NOT READY — SEE #1619**')).toBe(true);
    expect(source.includes('READY AFTER CANONICAL RECORD RECONCILIATION')).toBe(false);
  });

  it('keeps actual buyer turnover pending and payment processing disabled', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Buyer operational turnover: **PENDING IDENTIFIED BUYER AND PARTY ACCEPTANCE**')).toBe(true);
    expect(source.includes('**PAYMENT PROCESSING:** DISABLED / FAIL CLOSED / DEFERRED TO NEW OWNER')).toBe(true);
  });

  it('keeps the canonical index pointed at the current release authority', () => {
    const source = readRepoFile('docs/canonical/CANONICAL_DOCUMENT_INDEX.md');
    expect(source.includes('`docs/CURRENT_RELEASE_STATUS.md` | CANONICAL RELEASE/FREEZE AUTHORITY')).toBe(true);
  });

  it('does not restore the obsolete P0 execution board as active authority', () => {
    const source = readRepoFile('docs/canonical/CANONICAL_DOCUMENT_INDEX.md');
    expect(source.includes('P0_EXECUTION_BOARD_20260528.md')).toBe(false);
  });
});
