// frontend/dashboards/src/auth/AuthProvider.jsx
// Wraps the app with MSAL's context provider.
// Initialises the MSAL PublicClientApplication once at module load.
import { MsalProvider } from "@azure/msal-react";
import { PublicClientApplication, EventType } from "@azure/msal-browser";
import { msalConfig } from "./msalConfig";

const msalInstance = new PublicClientApplication(msalConfig);

// Set active account from any previously-cached session on first load.
msalInstance.initialize().then(() => {
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length > 0 && !msalInstance.getActiveAccount()) {
    msalInstance.setActiveAccount(accounts[0]);
  }

  msalInstance.addEventCallback((event) => {
    if (
      event.eventType === EventType.LOGIN_SUCCESS ||
      event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS
    ) {
      const account = event.payload?.account;
      if (account) msalInstance.setActiveAccount(account);
    }
  });
});

/**
 * Wrap your app root with <AuthProvider> to enable MSAL hooks throughout.
 */
export default function AuthProvider({ children }) {
  return <MsalProvider instance={msalInstance}>{children}</MsalProvider>;
}
