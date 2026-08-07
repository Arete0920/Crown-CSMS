import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { CROWN_LOGOS, CROWN_UI_LOGOS } from '../brand/crownBrandAssets';
import {
  getMicrosoftLogoPath,
  MICROSOFT_ASSET_STATUS,
  MICROSOFT_LOGOS,
} from '../brand/microsoftBrandAssets';

const projectRoot = process.cwd();
const readProjectFile = (filePath) => readFileSync(path.resolve(projectRoot, filePath), 'utf8');

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
  it('uses the shared CROWN icon component instead of letter navigation glyphs', () => {
    const sidebar = readProjectFile('src/components/launch/CrownSidebar.jsx');

    expect(sidebar).not.toContain('glyph:');
    expect(sidebar).toContain('CrownIcon');
  });

  it.each(['microsoft365', 'teams', 'outlook', 'word', 'excel', 'onedrive'])(
    'uses an approved Microsoft-hosted product logo for %s',
    (product) => {
      const asset = MICROSOFT_LOGOS[product];
      expect(asset.status).toBe(MICROSOFT_ASSET_STATUS.APPROVED);
      expect(asset.url).toMatch(/^https:\/\/res-1\.cdn\.office\.net\//);
      expect(asset.url).toMatch(/_48x1\.svg$/);
      expect(getMicrosoftLogoPath(product)).toBe(asset.url);
    },
  );

  it('never renders ambiguous single-letter Microsoft product placeholders', () => {
    const productLogo = readProjectFile('src/components/brand/MicrosoftProductLogo.jsx');

    expect(productLogo).not.toContain('FALLBACK_GLYPHS');
    expect(productLogo).not.toMatch(/teams:\s*['"]T['"]/);
    expect(productLogo).not.toMatch(/outlook:\s*['"]O['"]/);
    expect(productLogo).not.toMatch(/word:\s*['"]W['"]/);
    expect(productLogo).not.toMatch(/excel:\s*['"]X['"]/);
    expect(productLogo).toContain('CrownIcon');
    expect(productLogo).toContain('displayLabel');
  });

  it('preserves profile-avatar rendering with initials fallback', () => {
    const hero = readProjectFile('src/components/crown-dashboard/CrownHeroHeader.jsx');

    expect(hero).toContain('userAvatar = null');
    expect(hero).toContain('launch-hero-avatar-img');
    expect(hero).toContain('launch-hero-user-avatar');
    expect(hero).toContain('setAvatarFailed(true)');
  });

  it('maps all UI placements back to the canonical CROWN logo system', () => {
    expect(CROWN_UI_LOGOS.sidebarExpanded).toBe(CROWN_LOGOS.horizontal);
    expect(CROWN_UI_LOGOS.sidebarCollapsed).toBe(CROWN_LOGOS.mark);
    expect(CROWN_UI_LOGOS.topnavHorizontal).toBe(CROWN_LOGOS.horizontal);
    expect(CROWN_UI_LOGOS.loginBrand).toBe(CROWN_LOGOS.primaryStacked);
    expect(CROWN_UI_LOGOS.dashboardHero).toBe(CROWN_LOGOS.horizontal);
    expect(Object.values(CROWN_UI_LOGOS).every((assetPath) => assetPath.startsWith('/brand/crown/logo/'))).toBe(true);
  });

  it('ships nine distinct canonical logo variants with the current descriptor', () => {
    const logoContents = CANONICAL_LOGOS.map((file) => (
      readProjectFile(`public/brand/crown/logo/${file}`)
    ));

    expect(new Set(logoContents).size).toBe(CANONICAL_LOGOS.length);
    expect(logoContents.join('\n')).toContain('CHRISTIAN SCHOOL MANAGEMENT SOLUTION');
  });

  it('presents a labeled Microsoft 365 Education launcher', () => {
    const hero = readProjectFile('src/components/crown-dashboard/CrownHeroHeader.jsx');

    expect(hero).toContain('Microsoft 365 Education');
    expect(hero).toContain('Microsoft Teams');
    expect(hero).toContain('Microsoft Outlook');
    expect(hero).toContain('Microsoft Word');
    expect(hero).toContain('Microsoft Excel');
    expect(hero).toContain('Microsoft OneDrive');
  });
});
