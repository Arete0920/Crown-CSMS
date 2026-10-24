import { Navigate, useLocation } from "react-router";
import { getAccessToken } from "../../utils/authClient.js";

/**
 * Enforce a bearer-session prerequisite without selecting a school tenant.
 *
 * This is a UX guard only. Every platform API independently requires an active
 * superuser through IsPlatformOperator; client roles are never authority.
 */
export default function AuthenticatedPlatformRouteGuard({ children }) {
  const location = useLocation();
  if (!getAccessToken()) {
    return (
      <Navigate
        to="/not-authorized"
        replace
        state={{ from: location.pathname }}
      />
    );
  }
  return children;
}
