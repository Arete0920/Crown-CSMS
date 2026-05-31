import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DASHBOARD_REGISTRY } from '../config/dashboardRegistry';
import { WIZARD_REGISTRY } from '../routes/wizards';

const READY_STATES = new Set(['ready', 'live', 'production']);
const EVIDENCE_FRESHNESS_SLA_DAYS = 14;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const statusPath = path.resolve(__dirname, '../../../../docs/CURRENT_RELEASE_STATUS.md');
const statusSource = readFileSync(statusPath, 'utf8');

function parseCanonicalMetadata(markdown) {
  const candidateMatch = markdown.match(/- Candidate SHA: `([a-f0-9]{40})`/i);
  const branchMatch = markdown.match(/- Release authority branch: `([^`]+)`/i);

  return {
    candidateSha: candidateMatch?.[1] || '',
    releaseBranch: branchMatch?.[1] || '',
  };
}

const canonical = parseCanonicalMetadata(statusSource);

function isReadyEntry(entry) {
  const state = String(entry?.releaseState || '').trim().toLowerCase();
  return READY_STATES.has(state);
}

function validateEvidence(entry) {
  expect(entry.evidence).toBeTruthy();
  expect(typeof entry.evidence).toBe('object');

  const { artifact, collectedAt, candidateSha, releaseBranch } = entry.evidence;

  expect(typeof artifact).toBe('string');
  expect(artifact.trim().length).toBeGreaterThan(0);

  expect(typeof collectedAt).toBe('string');
  const collectedAtDate = new Date(collectedAt);
  expect(Number.isNaN(collectedAtDate.getTime())).toBe(false);

  const ageMs = Date.now() - collectedAtDate.getTime();
  const maxAgeMs = EVIDENCE_FRESHNESS_SLA_DAYS * 24 * 60 * 60 * 1000;
  expect(ageMs).toBeLessThanOrEqual(maxAgeMs);

  expect(candidateSha).toBe(canonical.candidateSha);
  expect(releaseBranch).toBe(canonical.releaseBranch);
}

describe('release readiness evidence contracts', () => {
  it('does not allow dashboard entries to be ready by default without evidence', () => {
    DASHBOARD_REGISTRY.forEach((entry) => {
      if (!entry.evidence) {
        expect(isReadyEntry(entry)).toBe(false);
      }
    });
  });

  it('does not allow wizard entries to be ready by default without evidence', () => {
    WIZARD_REGISTRY.forEach((entry) => {
      if (!entry.evidence) {
        expect(isReadyEntry(entry)).toBe(false);
      }
    });
  });

  it('enforces evidence schema/freshness/sha/branch for ready dashboards', () => {
    DASHBOARD_REGISTRY.filter(isReadyEntry).forEach(validateEvidence);
  });

  it('enforces evidence schema/freshness/sha/branch for ready wizards', () => {
    WIZARD_REGISTRY.filter(isReadyEntry).forEach(validateEvidence);
  });
});
