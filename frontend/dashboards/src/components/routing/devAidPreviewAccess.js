// A single isolated DEV preview route. Never grants backend authorization.
export const DEV_AID_PREVIEW_ORIGIN =
  "https://yellow-forest-0eecc8b0f-devcertification.eastus2.7.azurestaticapps.net";

export function canExposeDevAidWizard(route, { flag, sandboxMode, demoMode, origin } = {}) {
  return flag === "1"
    && sandboxMode === "1"
    && demoMode === "sandbox"
    && origin === DEV_AID_PREVIEW_ORIGIN
    && route?.path === "/aid-setup"
    && route?.moduleType === "wizard"
    && route?.releaseState === "draft";
}
