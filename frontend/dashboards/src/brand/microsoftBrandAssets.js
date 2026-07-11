export const MICROSOFT_ASSET_POLICY = 'Official Microsoft assets only. No placeholders, generated substitutes, recolors, or traced logos.';

export const MICROSOFT_ASSET_STATUS = {
  UNVERIFIED: 'unverified',
  APPROVED: 'approved',
};

export const MICROSOFT_LOGOS = {
  microsoft365: {
    path: '/brand/third-party/microsoft/microsoft-365/microsoft-365-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  teams: {
    path: '/brand/third-party/microsoft/apps/teams-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  outlook: {
    path: '/brand/third-party/microsoft/apps/outlook-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  word: {
    path: '/brand/third-party/microsoft/apps/word-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  excel: {
    path: '/brand/third-party/microsoft/apps/excel-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  powerpoint: {
    path: '/brand/third-party/microsoft/apps/powerpoint-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  onenote: {
    path: '/brand/third-party/microsoft/apps/onenote-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  onedrive: {
    path: '/brand/third-party/microsoft/apps/onedrive-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  sharepoint: {
    path: '/brand/third-party/microsoft/apps/sharepoint-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  forms: {
    path: '/brand/third-party/microsoft/apps/forms-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  planner: {
    path: '/brand/third-party/microsoft/apps/planner-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  bookings: {
    path: '/brand/third-party/microsoft/apps/bookings-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  entra: {
    path: '/brand/third-party/microsoft/identity-security/entra-id-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  azure: {
    path: '/brand/third-party/microsoft/identity-security/azure-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  intune: {
    path: '/brand/third-party/microsoft/identity-security/intune-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  defender: {
    path: '/brand/third-party/microsoft/identity-security/defender-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
  microsoftEducation: {
    path: '/brand/third-party/microsoft/education/microsoft-education-logo.svg',
    status: MICROSOFT_ASSET_STATUS.UNVERIFIED,
  },
};

export function getMicrosoftLogoPath(product) {
  const logo = MICROSOFT_LOGOS[product];
  if (!logo || logo.status !== MICROSOFT_ASSET_STATUS.APPROVED) return null;
  return logo.path;
}

export function getMicrosoftLogoStatus(product) {
  return MICROSOFT_LOGOS[product]?.status || MICROSOFT_ASSET_STATUS.UNVERIFIED;
}
