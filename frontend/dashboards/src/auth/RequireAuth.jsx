// frontend/dashboards/src/auth/RequireAuth.jsx
// Gate component: redirects to Microsoft login if user is not authenticated.
// Use this to wrap any route or component that requires sign-in.
//
// Usage:
//   <Route path="/dash/:role" element={<RequireAuth><RoleDashboardPage /></RequireAuth>} />
import React from "react";
import { useMsal, useIsAuthenticated } from "@azure/msal-react";
import { loginRequest } from "./msalConfig";

export default function RequireAuth({ children }) {
  const { instance, inProgress } = useMsal();
  const isAuthenticated = useIsAuthenticated();

  React.useEffect(() => {
    // Only redirect when MSAL has finished initialising and user is not signed in.
    if (!isAuthenticated && inProgress === "none") {
      instance.loginRedirect(loginRequest).catch((err) => {
        console.error("[RequireAuth] loginRedirect failed:", err);
      });
    }
  }, [isAuthenticated, inProgress, instance]);

  if (!isAuthenticated) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh" }}>
        <p style={{ color: "#888" }}>Redirecting to Microsoft sign-in…</p>
      </div>
    );
  }

  return children;
}
