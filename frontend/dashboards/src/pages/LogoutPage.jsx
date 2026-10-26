import { useEffect } from "react";
import { useNavigate } from "react-router";
import { clearBrowserAuthState } from "../utils/authClient.js";

export default function LogoutPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Clear credentials before changing routes. A child <Navigate> could
    // navigate before the former parent's passive cleanup effect executed.
    clearBrowserAuthState();
    navigate("/login", { replace: true });
  }, [navigate]);

  return null;
}
