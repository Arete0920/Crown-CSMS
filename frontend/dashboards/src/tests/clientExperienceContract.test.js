import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readProjectFile = (path) => readFileSync(resolve(path), 'utf8');

const CANONICAL_LOGOS = [
  'crown-logo-primary-stacked-full-color.svg',
  'crown-logo-horizontal-full-color.svg',
  'crown-logo-compact-full-color.svg',
  'crown-logo-wordmark-full-color.svg',
  'crown-logo-mark-crown-only.svg',
  'crown-logo-mark-shield.svg',
  'crown-logo-mark-square.svg',
  'crown-logo-monochrome-royal.svg',
  'crown-logo-monochrome-white.svg',
];

describe('shared client experience contract', () => {
  it('uses icon components instead of letter navigation glyphs', () => {
    const sidebar = readProjectFile('src/components/launch/CrownSidebar.jsx');

    expect(sidebar).not.toContain('glyph:');
    expect(sidebar).toContain('CrownIcon');
  });

  it('never renders single-letter Microsoft product placeholders', () => {
    const productLogo = readProjectFile('src/components/brand/MicrosoftProductLogo.jsx');
    const hero = readProjectFile('src/components/crown-dashboard/CrownHeroHeader.jsx');

    expect(productLogo).not.toContain('FALLBACK_GLYPHS');
    expect(productLogo).toContain('displayLabel');
    expect(hero).toContain('Microsoft 365 Education');
    expect(hero).toContain('Teams');
    expect(hero).toContain('Outlook');
    expect(hero).toContain('Word');
    expect(hero).toContain('Excel');
  });

  it('maps all UI placements back to the canonical CROWN logo system', () => {
    const assetMap = readProjectFile('src/brand/crownBrandAssets.js');

    expect(assetMap).not.toContain('/brand/crown/ui/');
    expect(assetMap).toContain('sidebarExpanded: CROWN_LOGOS.horizontal');
    expect(assetMap).toContain('loginBrand: CROWN_LOGOS.primaryStacked');
    expect(assetMap).toContain('dashboardHero: CROWN_LOGOS.horizontal');
  });

  it('ships nine distinct canonical logo variants', () => {
    const logoContents = CANONICAL_LOGOS.map((file) => (
      readProjectFile(`public/brand/crown/logo/${file}`)
    ));

    expect(new Set(logoContents).size).toBe(CANONICAL_LOGOS.length);
    expect(logoContents.join('\n')).toContain('CHRISTIAN SCHOOL MANAGEMENT SOLUTION');
  });
});
