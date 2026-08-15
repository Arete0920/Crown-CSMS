import { Navigate } from "react-router";
import {
  getReleaseState,
  getSafeFallbackPath,
  isCertificationState,
  isProductionReady,
} from "../../config/releaseState";

const CERTIFICATION_ACCESS_ENABLED = import.meta.env.VITE_WIZARD_CERTIFICATION === "1";

export default function ReleaseStateRoute({ route, children, fallbackPath }) {
  if (isProductionReady(route) || (CERTIFICATION_ACCESS_ENABLED && isCertificationState(route))) {
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
