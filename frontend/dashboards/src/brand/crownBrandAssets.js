export const CROWN_BRAND = {
  name: 'CROWN',
  descriptor: 'Christian School Management Solution',
  theme: 'light-royal',
};

export const CROWN_LOGOS = {
  primaryStacked: '/brand/crown/logo/crown-logo-primary-stacked-full-color.svg',
  horizontal: '/brand/crown/logo/crown-logo-horizontal-full-color.svg',
  compact: '/brand/crown/logo/crown-logo-compact-full-color.svg',
  wordmark: '/brand/crown/logo/crown-logo-wordmark-full-color.svg',
  mark: '/brand/crown/logo/crown-logo-mark-crown-only.svg',
  shield: '/brand/crown/logo/crown-logo-mark-shield.svg',
  squareMark: '/brand/crown/logo/crown-logo-mark-square.svg',
  monochromeRoyal: '/brand/crown/logo/crown-logo-monochrome-royal.svg',
  monochromeWhite: '/brand/crown/logo/crown-logo-monochrome-white.svg',
};

export const CROWN_UI_LOGOS = {
  sidebarExpanded: '/brand/crown/ui/crown-sidebar-expanded.svg',
  sidebarCollapsed: '/brand/crown/ui/crown-sidebar-collapsed.svg',
  topnavHorizontal: '/brand/crown/ui/crown-topnav-horizontal.svg',
  loginBrand: '/brand/crown/ui/crown-login-brand.svg',
  dashboardHero: '/brand/crown/ui/crown-dashboard-hero-logo.svg',
  printHeader: '/brand/crown/ui/crown-print-header-logo.svg',
  emailHeader: '/brand/crown/ui/crown-email-header-logo.svg',
  reportCover: '/brand/crown/ui/crown-report-cover-logo.svg',
};

export function getCrownLogoPath(variant = 'horizontal') {
  return CROWN_LOGOS[variant] || CROWN_LOGOS.horizontal;
}

export function getCrownUiLogoPath(placement = 'topnavHorizontal') {
  return CROWN_UI_LOGOS[placement] || CROWN_UI_LOGOS.topnavHorizontal;
}
