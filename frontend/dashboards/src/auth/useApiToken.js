// frontend/dashboards/src/auth/useApiToken.js
// Hook: returns an async function that acquires a fresh Microsoft access token.
// Falls back to silent acquisition; falls through to interactive popup on failure.
//
// Usage inside a component:
//   const getToken = useApiToken();
//   const token = await getToken();
import { useMsal } from "@azure/msal-react";
import { apiRequest } from "./msalConfig";

/**
 * Returns an async `getToken()` function.
 * The token can be attached as a Bearer header for Crown API calls.
 */
export function useApiToken() {
  const { instance, accounts } = useMsal();

  return async function getToken() {
    const account = instance.getActiveAccount() || accounts?.[0];
    if (!account) {
      throw new Error("No signed-in Microsoft account. Please sign in.");
    }

    try {
      const result = await instance.acquireTokenSilent({ ...apiRequest, account });
      return result.accessToken;
    } catch {
      // Silent acquisition failed (e.g. token expired, consent needed).
      const result = await instance.acquireTokenPopup({ ...apiRequest, account });
      return result.accessToken;
    }
  };
}
