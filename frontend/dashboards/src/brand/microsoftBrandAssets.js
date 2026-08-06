export const MICROSOFT_ASSET_POLICY = 'Official Microsoft-hosted product assets only. No placeholders, generated substitutes, recolors, or traced logos.';

export const MICROSOFT_ASSET_STATUS = {
  UNVERIFIED: 'unverified',
  APPROVED: 'approved',
};

const MICROSOFT_PRODUCT_ICON_CDN = 'https://res-1.cdn.office.net/files/fabric-cdn-prod_20230815.002/assets/brand-icons/product/svg';

function approvedProductIcon(fileName) {
  return {
    path: `${MICROSOFT_PRODUCT_ICON_CDN}/${fileName}`,
    status: MICROSOFT_ASSET_STATUS.APPROVED,
    source: 'Microsoft Office CDN',
  };
}

export const MICROSOFT_LOGOS = {
  microsoft365: approvedProductIcon('office_48x1.svg'),
  teams: approvedProductIcon('teams_48x1.svg'),
  outlook: approvedProductIcon('outlook_48x1.svg'),
  word: approvedProductIcon('word_48x1.svg'),
  excel: approvedProductIcon('excel_48x1.svg'),
  onedrive: approvedProductIcon('onedrive_48x1.svg'),
  powerpoint: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
  onenote: { path: null, status: MICROSOFT_ASSET_STATUS.UNVERIFIED },
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
