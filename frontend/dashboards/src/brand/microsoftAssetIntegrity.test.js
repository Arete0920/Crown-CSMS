import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { MICROSOFT_LOGOS } from './microsoftBrandAssets';

const testDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(testDir, '..', '..');
const microsoftPublicRoot = path.resolve(
  projectRoot,
  'public',
  'brand',
  'third-party',
  'microsoft'
);
const manifestPath = path.join(microsoftPublicRoot, 'manifest.json');

function getManifest() {
  return JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
}

function resolvePublicAsset(absoluteAssetPath) {
  const normalized = String(absoluteAssetPath || '').trim();
  const requiredPrefix = '/brand/third-party/microsoft/';
  if (!normalized.startsWith(requiredPrefix)) return null;

  const relativePath = normalized.slice(requiredPrefix.length);
  if (!relativePath || relativePath.split('/').includes('..')) return null;

  const resolved = path.resolve(microsoftPublicRoot, ...relativePath.split('/'));
  const relativeToRoot = path.relative(microsoftPublicRoot, resolved);
  if (relativeToRoot.startsWith('..') || path.isAbsolute(relativeToRoot)) return null;

  return resolved;
}

function existsCaseSensitive(filePath) {
  if (!fs.existsSync(filePath)) return false;

  const resolved = path.resolve(filePath);
  const parsed = path.parse(resolved);
  const segments = resolved.slice(parsed.root.length).split(path.sep).filter(Boolean);

  let current = parsed.root;
  for (const segment of segments) {
    const entries = fs.readdirSync(current);
    if (!entries.includes(segment)) return false;
    current = path.join(current, segment);
  }

  return fs.statSync(resolved).isFile();
}

function collectReferencedAssets() {
  const refs = [];

  for (const [name, def] of Object.entries(MICROSOFT_LOGOS)) {
    if (typeof def.path === 'string' && def.path.trim()) {
      refs.push({ source: 'microsoftBrandAssets', name, path: def.path.trim() });
    }
  }

  const manifest = getManifest();
  for (const [name, def] of Object.entries(manifest.assets || {})) {
    if (typeof def.path === 'string' && def.path.trim()) {
      refs.push({ source: 'manifest', name, path: def.path.trim() });
    }
  }

  return refs;
}

describe('Microsoft asset integrity', () => {
  it('ensures every referenced local Microsoft asset is contained and exists with exact case', () => {
    const invalid = collectReferencedAssets().filter((ref) => {
      const filePath = resolvePublicAsset(ref.path);
      return !filePath || !existsCaseSensitive(filePath);
    });

    expect(
      invalid,
      `Invalid Microsoft asset path references detected:\n${invalid
        .map((ref) => `${ref.source}:${ref.name}:${ref.path}`)
        .join('\n')}`
    ).toEqual([]);
  });
});
