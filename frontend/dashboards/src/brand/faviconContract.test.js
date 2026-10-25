import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

import { CROWN_LOGOS } from './crownBrandAssets';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const iconHref = '/brand/crown/logo/crown-logo-mark-shield.svg';

describe('CROWN browser icon contract', () => {
  it('declares the canonical brand-owned shield icon in the HTML entrypoint', () => {
    const html = fs.readFileSync(path.join(projectRoot, 'index.html'), 'utf8');

    expect(CROWN_LOGOS.shield).toBe(iconHref);
    expect(html).toContain(
      '<link rel="icon" type="image/svg+xml" href="/brand/crown/logo/crown-logo-mark-shield.svg" />'
    );
  });

  it('ships a self-contained local icon without external or executable content', () => {
    const icon = path.join(projectRoot, 'public', iconHref.slice(1));
    const svg = fs.readFileSync(icon, 'utf8');
    const imageHrefs = [...svg.matchAll(/<image\b[^>]*href="([^"]+)"/gi)].map((match) => match[1]);

    expect(svg).toMatch(/<svg\b/);
    expect(svg).toMatch(/viewBox="0 0 500 480"/);
    expect(svg).not.toMatch(/<script\b/i);
    expect(imageHrefs.length).toBeGreaterThan(0);
    expect(imageHrefs.every((href) => href.startsWith('data:image/png;base64,'))).toBe(true);
  });
});
