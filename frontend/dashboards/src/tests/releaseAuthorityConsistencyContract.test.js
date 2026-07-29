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
  it('keeps the canonical production decision at not approved / no-go / hold', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Production: **NOT APPROVED / NO-GO / HOLD**')).toBe(true);
    expect(source.includes('**PRODUCTION DECISION: NOT APPROVED / NO-GO / HOLD**')).toBe(true);
    expect(source.includes('**CURRENT DECISION: PRODUCTION AUTHORIZED**')).toBe(false);
  });

  it('keeps buyer turnover and payment processing unapproved', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Buyer operational turnover: **NOT APPROVED**')).toBe(true);
    expect(source.includes('**PAYMENT PROCESSING: DISABLED / FAIL CLOSED**')).toBe(true);
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
