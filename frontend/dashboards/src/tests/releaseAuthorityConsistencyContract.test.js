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
  it('keeps canonical production decision as NOT APPROVED', () => {
    const source = readRepoFile('docs/CURRENT_RELEASE_STATUS.md');
    expect(source.includes('Repository-wide decision: **SANDBOX_RELEASE_CANDIDATE**.')).toBe(true);
    expect(source.includes('Production release decision: **NOT APPROVED**.')).toBe(true);
  });

  it('keeps current scorecard decision as NO-GO', () => {
    const source = readRepoFile('docs/release/CURRENT_RELEASE_SCORECARD_20260528.md');
    expect(source.includes('Current decision: NO-GO')).toBe(true);
  });

  it('keeps P0 board canonical baseline aligned to NO-GO', () => {
    const source = readRepoFile('docs/release/P0_EXECUTION_BOARD_20260528.md');
    expect(source.includes('Repository-wide decision is NO-GO')).toBe(true);
  });

  it('blocks known contradictory unrestricted-go approved-slice wording in P0 board', () => {
    const source = readRepoFile('docs/release/P0_EXECUTION_BOARD_20260528.md');
    expect(source.includes('approved slice remains `UNRESTRICTED GO`')).toBe(false);
    expect(source.includes('canonical approved-slice release authority remains unchanged (`UNRESTRICTED GO`)')).toBe(false);
  });
});
