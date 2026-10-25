import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

const assetRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'public', 'brand', 'crown', 'logo');
const sourceMap = {
  'crown-logo-mark-square.svg': 'crown-logo-mark-crown-only.svg',
  'crown-logo-monochrome-royal.svg': 'crown-logo-horizontal-full-color.svg',
  'crown-logo-monochrome-white.svg': 'crown-logo-horizontal-full-color.svg',
};

describe('CROWN standalone SVG image variants', () => {
  for (const [variant, canonical] of Object.entries(sourceMap)) {
    it(`${variant} embeds the canonical source without a relative external image`, () => {
      const svg = fs.readFileSync(path.join(assetRoot, variant), 'utf8');
      const original = fs.readFileSync(path.join(assetRoot, canonical), 'utf8');
      const imageHrefs = [...svg.matchAll(/<image\\b[^>]*\\bhref="([^"]+)"/gi)].map((match) => match[1]);
      expect(imageHrefs).toHaveLength(1);
      expect(imageHrefs[0].startsWith('data:image/svg+xml;charset=utf-8,')).toBe(true);
      expect(decodeURIComponent(imageHrefs[0].split(',', 2)[1])).toBe(original);
      expect(svg).not.toMatch(/<script\\b/i);
    });
  }
});
