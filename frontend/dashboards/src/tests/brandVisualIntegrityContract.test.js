import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { CROWN_LOGOS, CROWN_UI_LOGOS } from '../brand/crownBrandAssets';
import {
  MICROSOFT_ASSET_STATUS,
  MICROSOFT_LOGOS,
} from '../brand/microsoftBrandAssets';

const microsoftProductLogoSource = readFileSync(
  new URL('../components/brand/MicrosoftProductLogo.jsx', import.meta.url),
  'utf8',
);

const heroHeaderSource = readFileSync(
  new URL('../components/crown-dashboard/CrownHeroHeader.jsx', import.meta.url),
  'utf8',
);

describe('buyer-facing brand visual integrity', () => {
  it('uses canonical CROWN artwork for every shared UI placement', () => {
    expect(CROWN_UI_LOGOS.sidebarExpanded).toBe(CROWN_LOGOS.horizontal);
    expect(CROWN_UI_LOGOS.sidebarCollapsed).toBe(CROWN_LOGOS.mark);
    expect(CROWN_UI_LOGOS.topnavHorizontal).toBe(CROWN_LOGOS.horizontal);
    expect(CROWN_UI_LOGOS.loginBrand).toBe(CROWN_LOGOS.primaryStacked);
    expect(CROWN_UI_LOGOS.dashboardHero).toBe(CROWN_LOGOS.monochromeWhite);
  });

  it.each(['teams', 'outlook', 'word', 'excel', 'onedrive'])(
    'uses an approved Microsoft-hosted product logo for %s',
    (product) => {
      const asset = MICROSOFT_LOGOS[product];
      expect(asset.status).toBe(MICROSOFT_ASSET_STATUS.APPROVED);
      expect(asset.path).toMatch(/^https:\/\/res-1\.cdn\.office\.net\//);
      expect(asset.path).toMatch(/_48x1\.svg$/);
    },
  );

  it('never substitutes ambiguous Microsoft application initials', () => {
    expect(microsoftProductLogoSource).not.toContain('FALLBACK_GLYPHS');
    expect(microsoftProductLogoSource).not.toMatch(/teams:\s*['"]T['"]/);
    expect(microsoftProductLogoSource).not.toMatch(/outlook:\s*['"]O['"]/);
    expect(microsoftProductLogoSource).not.toMatch(/word:\s*['"]W['"]/);
    expect(microsoftProductLogoSource).not.toMatch(/excel:\s*['"]X['"]/);
    expect(microsoftProductLogoSource).toContain('{displayLabel}');
  });

  it('presents a labeled Microsoft 365 Education launcher', () => {
    expect(heroHeaderSource).toContain('Microsoft 365 Education');
    expect(heroHeaderSource).toContain('Open Microsoft');
    expect(heroHeaderSource).not.toContain('label="Calendar"');
  });
});
