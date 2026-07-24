import { useEffect } from "react";
import { Navigate } from "react-router";

const STORAGE_KEYS = [
  "crown.jwt.access",
  "crown.role",
  "crown.school.id",
  "crown.demo.role",
  "schoolId",
  "crown_user_roles",
  "crown_current_user",
];

function clearBrowserAuthState() {
  for (const storage of [sessionStorage, localStorage]) {
    try {
      for (const key of STORAGE_KEYS) {
        storage.removeItem(key);
      }
    } catch {
      // Ignore storage access failures and continue redirecting to login.
    }
  }
}

export default function LogoutPage() {
  useEffect(() => {
    clearBrowserAuthState();
  }, []);

  return <Navigate to="/login" replace />;
}
