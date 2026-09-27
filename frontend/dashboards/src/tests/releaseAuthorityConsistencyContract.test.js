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
  it('keeps the August certification historical and current release status exact-head based', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('The August 18, 2026 engineering certification remains historical evidence for that certified baseline.')).toBe(true);
    expect(source.includes('exact-head verification')).toBe(true);
    expect(source.includes('No successor production tag or release is asserted by this record.')).toBe(true);
    expect(source.includes('Current buyer diligence package: **NOT READY')).toBe(false);
  });

  it('keeps production operation and payment activation separate from repository readiness', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Repository release readiness is separate from environment-specific production operation.')).toBe(true);
    expect(source.includes('**PAYMENT PROCESSING: DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**')).toBe(true);
  });

  it('keeps the canonical index pointed at current release and investor-diligence authority', () => {
    const source = readRepoFile('docs/canonical/CANONICAL_DOCUMENT_INDEX.md');
    expect(source.includes('docs/CURRENT_RELEASE_STATUS.md')).toBe(true);
    expect(source.includes('docs/INVESTOR_TECHNICAL_REVIEW_GUIDE.md')).toBe(true);
    expect(source.includes('Current release, payment, recovery, and turnover posture')).toBe(true);
  });

  it('does not restore obsolete execution-board authority', () => {
    const source = readRepoFile('docs/canonical/CANONICAL_DOCUMENT_INDEX.md');
    expect(source.includes('P0_EXECUTION_BOARD_20260528.md')).toBe(false);
  });
});
