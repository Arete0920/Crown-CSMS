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
  it('keeps completed engineering authority distinct from transaction-time operational turnover', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Successor migration and engineering gap-closure program: **COMPLETED / HISTORICAL PROGRAM RECORD**')).toBe(true);
    expect(source.includes('Repository engineering completion and production-ready source certification are distinct from transaction-time deployment and successor operational transfer.')).toBe(true);
    expect(source.includes('Buyer operational turnover: **POST-CONTRACT / PENDING AUTHORIZED PARTY ACCEPTANCE**')).toBe(true);
    expect(source.includes('issue #14 remains the controlling turnover record')).toBe(false);
    expect(source.includes('Current buyer diligence package: **NOT READY')).toBe(false);
  });

  it('keeps actual buyer turnover pending and payment processing disabled', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Buyer operational turnover: **POST-CONTRACT / PENDING AUTHORIZED PARTY ACCEPTANCE**')).toBe(true);
    expect(source.includes('**PAYMENT PROCESSING: DISABLED / FAIL CLOSED / NOT AUTHORIZED FOR ACTIVATION**')).toBe(true);
  });

  it('keeps the canonical index pointed at the current release authority document', () => {
    const source = readRepoFile('docs/canonical/CANONICAL_DOCUMENT_INDEX.md');
    expect(source.includes('`docs/CURRENT_RELEASE_STATUS.md`')).toBe(true);
    expect(source.includes('Current production-ready engineering, release, payment, recovery, and turnover posture')).toBe(true);
    expect(source.includes('Current release status')).toBe(true);
  });

  it('does not restore the obsolete P0 execution board as active authority', () => {
    const source = readRepoFile('docs/canonical/CANONICAL_DOCUMENT_INDEX.md');
    expect(source.includes('P0_EXECUTION_BOARD_20260528.md')).toBe(false);
  });
});
