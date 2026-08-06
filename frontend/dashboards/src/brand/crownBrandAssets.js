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

// UI placements resolve only to canonical brand assets. Expanded client
// surfaces use the approved horizontal crown-and-cross lockup; the compact
// crown mark is reserved for collapsed navigation and icon-scale contexts.
export const CROWN_UI_LOGOS = {
  sidebarExpanded: CROWN_LOGOS.horizontal,
  sidebarCollapsed: CROWN_LOGOS.mark,
  topnavHorizontal: CROWN_LOGOS.horizontal,
  loginBrand: CROWN_LOGOS.primaryStacked,
  dashboardHero: CROWN_LOGOS.horizontal,
  printHeader: CROWN_LOGOS.horizontal,
  emailHeader: CROWN_LOGOS.horizontal,
  reportCover: CROWN_LOGOS.primaryStacked,
};

export function getCrownLogoPath(variant = 'horizontal') {
  return CROWN_LOGOS[variant] || CROWN_LOGOS.horizontal;
}

export function getCrownUiLogoPath(placement = 'topnavHorizontal') {
  return CROWN_UI_LOGOS[placement] || CROWN_UI_LOGOS.topnavHorizontal;
}
