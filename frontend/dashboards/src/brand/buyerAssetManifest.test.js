import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { CROWN_LOGOS } from './crownBrandAssets';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../../..');
const manifestPath = path.join(root, 'docs/brand/CROWN_BUYER_ASSET_REVIEW_MANIFEST.json');
const readManifest = () => JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

describe('CROWN buyer asset review manifest', () => {
  it('lists exactly the existing nine canonical logo paths, with current content checksums', () => {
    const manifest = readManifest();
    const canonical = Object.values(CROWN_LOGOS).map((url) => 'frontend/dashboards/public' + url);
    const entries = manifest.assets;
    expect(canonical).toHaveLength(9);
    expect(entries).toHaveLength(9);
    expect(new Set(entries.map((entry) => entry.path))).toEqual(new Set(canonical));

    for (const entry of entries) {
      const content = fs.readFileSync(path.join(root, entry.path));
      const actual = createHash('sha256').update(content).digest('hex');
      expect(entry.sha256, entry.path).toBe(actual);
      expect(entry.file_type).toBe('image/svg+xml');
      expect(entry.rights_status).toBe('UNVERIFIED');
      expect(entry.buyer_distribution).toBe('HOLD');
    }
  });

  it('prevents an unapproved review register from being labeled as buyer clearance', () => {
    const manifest = readManifest();
    expect(manifest.status).toBe('INTERNAL_REVIEW_ONLY_NOT_APPROVED_FOR_DISTRIBUTION');
    expect(manifest.approval_required_before_external_sharing).toBe(true);
    expect(manifest.rights_review).toBe('UNVERIFIED');
    expect(manifest.commercial_transfer_authority).toBe('NOT_APPROVED');
    expect(manifest.duplicate_alias_groups).toHaveLength(2);
  });
});
