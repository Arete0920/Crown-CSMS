import { Navigate, useLocation } from "react-router";
import { getAccessToken, getSelectedSchoolId } from "../../utils/authClient.js";

/**
 * UI-level denial for school dashboards without an active session/tenant.
 * The API MUST independently authorize every protected resource; client-side
 * session state is not evidence of an authenticated or permitted backend user.
 */
export default function AuthenticatedSchoolRouteGuard({ children }) {
  const location = useLocation();
  if (!getAccessToken() || !getSelectedSchoolId()) {
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
