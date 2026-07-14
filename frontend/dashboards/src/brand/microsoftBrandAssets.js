export const MICROSOFT_ASSET_POLICY = 'Official Microsoft assets only. No placeholders, generated substitutes, recolors, or traced logos.';

export const MICROSOFT_ASSET_STATUS = {
  UNVERIFIED: 'unverified',
  APPROVED: 'approved',
};

export const MICROSOFT_LOGOS = {
  microsoft365: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  teams: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  outlook: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  word: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  excel: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  powerpoint: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  onenote: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  onedrive: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  sharepoint: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  forms: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  planner: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  bookings: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  entra: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  azure: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  intune: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  defender: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  microsoftEducation: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
};

export function getMicrosoftLogoPath(product) {
  const logo = MICROSOFT_LOGOS[product];
  if (!logo || logo.status !== MICROSOFT_ASSET_STATUS.APPROVED) return null;
  return logo.path;
}

export function getMicrosoftLogoStatus(product) {
  return MICROSOFT_LOGOS[product]?.status || MICROSOFT_ASSET_STATUS.UNVERIFIED;
}
