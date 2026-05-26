=== BRAND ASSET INVENTORY ===
## Brand component usage anchors
frontend/dashboards/src\styles\launch-shell.css:36:  --launch-brand: var(--crown-primary-deep, #1d4ed8);
frontend/dashboards/src\styles\launch-shell.css:68:.launch-brand-lockup {
frontend/dashboards/src\styles\launch-shell.css:76:.launch-brand-crest {
frontend/dashboards/src\styles\launch-shell.css:84:.launch-brand-crest svg {
frontend/dashboards/src\styles\launch-shell.css:90:.launch-brand-title {
frontend/dashboards/src\styles\launch-shell.css:98:.launch-brand-tagline {
frontend/dashboards/src\styles\launch-shell.css:106:.crown-logo {
frontend/dashboards/src\styles\launch-shell.css:125:.crown-logo-sidebarExpanded {
frontend/dashboards/src\styles\launch-shell.css:129:.crown-logo-sidebarCollapsed,
frontend/dashboards/src\styles\launch-shell.css:135:.crown-logo-topnavHorizontal {
frontend/dashboards/src\styles\launch-shell.css:140:.crown-logo-loginBrand {
frontend/dashboards/src\styles\launch-shell.css:1531:  background: linear-gradient(90deg, var(--launch-accent), var(--launch-brand));
frontend/dashboards/src\brand\crownBrandAssets.js:8:  primaryStacked: '/brand/crown/logo/crown-logo-primary-stacked-full-color.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:9:  horizontal: '/brand/crown/logo/crown-logo-horizontal-full-color.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:10:  compact: '/brand/crown/logo/crown-logo-compact-full-color.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:11:  wordmark: '/brand/crown/logo/crown-logo-wordmark-full-color.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:12:  mark: '/brand/crown/logo/crown-logo-mark-crown-only.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:13:  shield: '/brand/crown/logo/crown-logo-mark-shield.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:14:  squareMark: '/brand/crown/logo/crown-logo-mark-square.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:15:  monochromeRoyal: '/brand/crown/logo/crown-logo-monochrome-royal.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:16:  monochromeWhite: '/brand/crown/logo/crown-logo-monochrome-white.svg',
frontend/dashboards/src\brand\crownBrandAssets.js:30:export function getCrownLogoPath(variant = 'horizontal') {
frontend/dashboards/src\components\brand\BrandLockup.jsx:1:import CrownLogo from './CrownLogo';
frontend/dashboards/src\components\brand\BrandLockup.jsx:4:export default function BrandLockup({
frontend/dashboards/src\components\brand\BrandLockup.jsx:12:        <CrownLogo variant="mark" alt={`${CROWN_BRAND.name} mark`} />
frontend/dashboards/src\components\brand\BrandLockup.jsx:19:      <CrownLogo placement={placement} />
frontend/dashboards/src\components\brand\CrownAppMark.jsx:1:import CrownLogo from './CrownLogo';
frontend/dashboards/src\components\brand\CrownAppMark.jsx:3:export default function CrownAppMark({ className = '', label = 'CROWN' }) {
frontend/dashboards/src\components\brand\CrownAppMark.jsx:6:      <CrownLogo variant="mark" alt="" className="crown-app-mark-image" />
frontend/dashboards/src\components\brand\CrownLogo.jsx:2:import { CROWN_BRAND, getCrownLogoPath, getCrownUiLogoPath } from '../../brand/crownBrandAssets';
frontend/dashboards/src\components\brand\CrownLogo.jsx:4:export default function CrownLogo({
frontend/dashboards/src\components\brand\CrownLogo.jsx:11:  const src = placement ? getCrownUiLogoPath(placement) : getCrownLogoPath(variant);
frontend/dashboards/src\components\brand\CrownLogo.jsx:33:      className={`crown-logo crown-logo-${placement || variant} ${className}`.trim()}
frontend/dashboards/src\components\brand\MicrosoftProductLogo.test.jsx:5:import MicrosoftProductLogo from './MicrosoftProductLogo';
frontend/dashboards/src\components\brand\MicrosoftProductLogo.test.jsx:11:describe('MicrosoftProductLogo', () => {
frontend/dashboards/src\components\brand\MicrosoftProductLogo.test.jsx:13:    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);
frontend/dashboards/src\components\brand\MicrosoftProductLogo.test.jsx:20:    render(<MicrosoftProductLogo product="teams" label="Microsoft Teams" />);
frontend/dashboards/src\components\brand\MicrosoftProductLogo.test.jsx:30:    render(<MicrosoftProductLogo product="unknown_app" label="Unknown App" />);
frontend/dashboards/src\components\brand\CrownLogo.test.jsx:5:import CrownLogo from './CrownLogo';
frontend/dashboards/src\components\brand\CrownLogo.test.jsx:11:describe('CrownLogo', () => {
frontend/dashboards/src\components\brand\CrownLogo.test.jsx:13:    render(<CrownLogo variant="horizontal" />);
frontend/dashboards/src\components\brand\CrownLogo.test.jsx:16:    expect(logo.getAttribute('src')).toBe('/brand/crown/logo/crown-logo-horizontal-full-color.svg');
frontend/dashboards/src\components\brand\CrownLogo.test.jsx:20:    render(<CrownLogo variant="horizontal" />);
frontend/dashboards/src\components\brand\MicrosoftProductLogo.jsx:4:export default function MicrosoftProductLogo({
frontend/dashboards/src\pages\LoginPage.jsx:3:import CrownLogo from "../components/brand/CrownLogo";
frontend/dashboards/src\pages\LoginPage.jsx:245:        .brand-mark .crown-logo-loginBrand {
frontend/dashboards/src\pages\LoginPage.jsx:527:              <CrownLogo placement="loginBrand" />
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:2:import CrownLogo from '../brand/CrownLogo';
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:3:import MicrosoftProductLogo from '../brand/MicrosoftProductLogo';
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:56:            <CrownLogo placement="dashboardHero" />
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:76:                <MicrosoftProductLogo product="teams" label="Teams" />
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:85:                <MicrosoftProductLogo product="outlook" label="Outlook" />
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:94:                <MicrosoftProductLogo product="microsoft365" label="Calendar" />
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:103:                <MicrosoftProductLogo product="word" label="Word" />
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:112:                <MicrosoftProductLogo product="excel" label="Excel" />
frontend/dashboards/src\components\crown-dashboard\CrownHeroHeader.jsx:121:                <MicrosoftProductLogo product="onedrive" label="OneDrive" />
frontend/dashboards/src\components\launch\CrownTopbar.jsx:2:import CrownLogo from '../brand/CrownLogo';
frontend/dashboards/src\components\launch\CrownTopbar.jsx:14:        <CrownLogo placement="topnavHorizontal" />
frontend/dashboards/src\components\launch\CrownSidebar.jsx:4:import BrandLockup from '../brand/BrandLockup';
frontend/dashboards/src\components\launch\CrownSidebar.jsx:121:      <BrandLockup placement="sidebarExpanded" />
## Brand files present
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown-logo-transparent.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown-mark-transparent.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\manifest.json
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\README.md
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-compact-full-color.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-horizontal-full-color.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-mark-crown-only.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-mark-shield.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-mark-square.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-monochrome-royal.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-monochrome-white.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-primary-stacked-full-color.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\logo\crown-logo-wordmark-full-color.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-dashboard-hero-logo.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-email-header-logo.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-login-brand.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-print-header-logo.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-report-cover-logo.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-sidebar-collapsed.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-sidebar-expanded.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\crown\ui\crown-topnav-horizontal.svg
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\third-party\microsoft\license-and-usage-notes.md
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\third-party\microsoft\manifest.json
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\third-party\microsoft\README.md
C:\Users\JMega\OneDrive\Desktop\Crown2026_deploypr\frontend\dashboards\public\brand\third-party\microsoft\usage\microsoft-logo-source-register.md
