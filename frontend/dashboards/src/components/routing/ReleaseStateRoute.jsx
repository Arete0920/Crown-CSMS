import { Navigate } from "react-router";
import {
  getReleaseState,
  getSafeFallbackPath,
  isProductionReady,
} from "../../config/releaseState";

const WIZARD_CERTIFICATION_ACCESS_ENABLED = import.meta.env.VITE_WIZARD_CERTIFICATION === "1";

export default function ReleaseStateRoute({ route, children, fallbackPath }) {
  const certificationAccess =
    WIZARD_CERTIFICATION_ACCESS_ENABLED && route?.moduleType === "wizard";

  if (isProductionReady(route) || certificationAccess) {
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
