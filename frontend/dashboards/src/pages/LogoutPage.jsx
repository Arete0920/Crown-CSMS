import { useEffect } from "react";
import { Navigate } from "react-router";
import { clearBrowserAuthState } from "../utils/authClient.js";

export default function LogoutPage() {
  useEffect(() => {
    clearBrowserAuthState();
  }, []);

  return <Navigate to="/login" replace />;
}
