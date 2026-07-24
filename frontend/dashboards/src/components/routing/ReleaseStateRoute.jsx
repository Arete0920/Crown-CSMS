import { Navigate } from "react-router";
import {
  getReleaseState,
  getSafeFallbackPath,
  isProductionReady,
} from "../../config/releaseState";

export default function ReleaseStateRoute({ route, children, fallbackPath }) {
  if (isProductionReady(route)) {
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
