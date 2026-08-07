import { readFileSync } from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { CROWN_LOGOS, CROWN_UI_LOGOS } from '../brand/crownBrandAssets';
import {
  getMicrosoftLogoPath,
  MICROSOFT_ASSET_STATUS,
  MICROSOFT_LOGOS,
} from '../brand/microsoftBrandAssets';
import {
  containsKnownDisplayMojibake,
  normalizeDisplayText,
} from '../utils/displayTextIntegrity.js';

const projectRoot = path.resolve('.');
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
  it('keeps the public sandbox evaluator outside the authenticated application shell', () => {
    const sandboxLanding = readProjectFile('src/pages/SandboxLandingPage.jsx');

    expect(sandboxLanding).not.toContain('CrownLayout');
    expect(sandboxLanding).not.toContain('authenticatedFetch');
    expect(sandboxLanding).toContain('sandbox-crown-layout');
    expect(sandboxLanding).toContain('Guided Proof Sandbox');
  });

  it('keeps the sandbox command center on the canonical CROWN client experience', () => {
    const commandCenter = readProjectFile('src/sandbox/SandboxCommandCenter.jsx');

    expect(commandCenter).not.toContain('<style');
    expect(commandCenter).not.toContain('--crown-compat-color-');
    expect(commandCenter).not.toContain('getTrackSchools');
    expect(commandCenter).not.toContain('Switch track');
    expect(commandCenter).toContain('CrownLogo');
    expect(commandCenter).toContain('CrownIcon');
    expect(commandCenter).toContain('sandbox-experience-header');
    expect(commandCenter).toContain('sandbox-experience-panel');
    expect(commandCenter).toContain('getSandboxLoginHref');
    expect(commandCenter).toContain('submitSandboxFeedback');
    expect(commandCenter).toContain('recordSandboxEvent');
    expect(commandCenter).toContain('Return to evaluator');
  });

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

  it.each([
    ['Teacher â€” English & History', 'Teacher — English & History'],
    ['Attendance â€“ daily review', 'Attendance – daily review'],
    ['Todayâ€™s priorities', 'Today’s priorities'],
    ['â€œFaithful service', '“Faithful service'],
    ['Moreâ€¦', 'More…'],
  ])('normalizes known display mojibake: %s', (input, expected) => {
    expect(containsKnownDisplayMojibake(input)).toBe(true);
    expect(normalizeDisplayText(input)).toBe(expected);
    expect(containsKnownDisplayMojibake(normalizeDisplayText(input))).toBe(false);
  });

  it('enforces display-text integrity across rendered text and accessibility labels', () => {
    const guard = readProjectFile('src/components/system/DisplayTextIntegrityGuard.jsx');
    const main = readProjectFile('src/main.jsx');
    const hero = readProjectFile('src/components/crown-dashboard/CrownHeroHeader.jsx');

    expect(main).toContain('DisplayTextIntegrityGuard');
    expect(guard).toContain('MutationObserver');
    expect(guard).toContain('characterData: true');
    expect(guard).toContain('attributeFilter: NORMALIZED_ATTRIBUTES');
    expect(guard).toContain("'aria-label'");
    expect(guard).toContain("'placeholder'");
    expect(hero).toContain('normalizeDisplayText');
    expect(hero).toContain('displayHeroMessage');
  });

  it('forces readable hero title and message contrast over legacy important rules', () => {
    const visualProof = readProjectFile('src/styles/visual-proof-integrity.css');

    expect(visualProof).toContain('.launch-hero-header .launch-hero-text .launch-hero-title');
    expect(visualProof).toMatch(/color:\s*var\(--crown-primary-deep\)\s*!important/);
    expect(visualProof).toContain('-webkit-text-fill-color: var(--crown-primary-deep) !important');
    expect(visualProof).toContain('.launch-hero-header .launch-hero-text .launch-hero-message');
    expect(visualProof).toMatch(/color:\s*var\(--crown-muted\)\s*!important/);
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
    logoContents.forEach((logoContent) => {
      expect(logoContent).toMatch(/christian school management solution/i);
    });
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
