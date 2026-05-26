export const MICROSOFT_ASSET_POLICY = 'Official Microsoft assets only. No placeholders, generated substitutes, recolors, or traced logos.';

export const MICROSOFT_LOGOS = {
  microsoft365: '/brand/third-party/microsoft/microsoft-365/microsoft-365-logo.svg',
  teams: '/brand/third-party/microsoft/apps/teams-logo.svg',
  outlook: '/brand/third-party/microsoft/apps/outlook-logo.svg',
  word: '/brand/third-party/microsoft/apps/word-logo.svg',
  excel: '/brand/third-party/microsoft/apps/excel-logo.svg',
  powerpoint: '/brand/third-party/microsoft/apps/powerpoint-logo.svg',
  onenote: '/brand/third-party/microsoft/apps/onenote-logo.svg',
  onedrive: '/brand/third-party/microsoft/apps/onedrive-logo.svg',
  sharepoint: '/brand/third-party/microsoft/apps/sharepoint-logo.svg',
  forms: '/brand/third-party/microsoft/apps/forms-logo.svg',
  planner: '/brand/third-party/microsoft/apps/planner-logo.svg',
  bookings: '/brand/third-party/microsoft/apps/bookings-logo.svg',
  entra: '/brand/third-party/microsoft/identity-security/entra-id-logo.svg',
  azure: '/brand/third-party/microsoft/identity-security/azure-logo.svg',
  intune: '/brand/third-party/microsoft/identity-security/intune-logo.svg',
  defender: '/brand/third-party/microsoft/identity-security/defender-logo.svg',
  microsoftEducation: '/brand/third-party/microsoft/education/microsoft-education-logo.svg',
};

export function getMicrosoftLogoPath(product) {
  return MICROSOFT_LOGOS[product] || null;
}
