import { Navigate } from "react-router";
import {
  getReleaseState,
  getSafeFallbackPath,
  isProductionReady,
} from "../../config/releaseState";

import { canExposeDevAidWizard } from "./devAidPreviewAccess.js";

const WIZARD_CERTIFICATION_ACCESS_ENABLED = import.meta.env.VITE_WIZARD_CERTIFICATION === "1";

export default function ReleaseStateRoute({ route, children, fallbackPath }) {
  const certificationAccess =
    WIZARD_CERTIFICATION_ACCESS_ENABLED && route?.moduleType === "wizard";

  const isolatedAidPreviewAccess = canExposeDevAidWizard(route, {
    flag: import.meta.env.VITE_DEV_AID_WIZARD_PREVIEW,
    sandboxMode: import.meta.env.VITE_SANDBOX_MODE,
    demoMode: import.meta.env.VITE_DEMO_MODE,
    origin: globalThis.location?.origin,
  });

  if (isProductionReady(route) || certificationAccess || isolatedAidPreviewAccess) {
    return children;
  }

  const target = fallbackPath || getSafeFallbackPath(route);
  const state = getReleaseState(route);

  return (
    <Navigate
      to={target}
      replace
      state={{
        blockedRoute: route?.path || route?.href || null,
        blockedReleaseState: state || "unknown",
      }}
    />
  );
}
