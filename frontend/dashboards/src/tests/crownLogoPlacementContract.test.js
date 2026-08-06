import { describe, expect, it } from 'vitest';
import { CROWN_LOGOS, CROWN_UI_LOGOS } from '../brand/crownBrandAssets';

describe('CROWN logo placement contract', () => {
  it('never returns the deprecated placement-specific artwork', () => {
    for (const assetPath of Object.values(CROWN_UI_LOGOS)) {
      expect(assetPath).toMatch(/^\/brand\/crown\/logo\//);
      expect(assetPath).not.toMatch(/^\/brand\/crown\/ui\//);
    }
  });

  it('uses the canonical approved presentation variants', () => {
    expect(CROWN_UI_LOGOS.sidebarExpanded).toBe(CROWN_LOGOS.horizontal);
    expect(CROWN_UI_LOGOS.sidebarCollapsed).toBe(CROWN_LOGOS.mark);
    expect(CROWN_UI_LOGOS.loginBrand).toBe(CROWN_LOGOS.primaryStacked);
    expect(CROWN_UI_LOGOS.dashboardHero).toBe(CROWN_LOGOS.monochromeWhite);
  });
});
