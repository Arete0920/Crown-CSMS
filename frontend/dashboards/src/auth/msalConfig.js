// frontend/dashboards/src/auth/msalConfig.js
// Microsoft Entra ID (Azure AD) MSAL configuration for PKCE/SPA flow.
// All values come from Vite env vars (set in .env.local for dev, App Settings for prod).

export const msalConfig = {
  auth: {
    clientId:                   import.meta.env.VITE_AAD_CLIENT_ID     || "",
    authority:                  `https://login.microsoftonline.com/${import.meta.env.VITE_AAD_TENANT_ID || "common"}`,
    redirectUri:                import.meta.env.VITE_AAD_REDIRECT_URI  || window.location.origin + "/auth/callback",
    postLogoutRedirectUri:      import.meta.env.VITE_AAD_POST_LOGOUT_REDIRECT_URI || window.location.origin + "/",
    navigateToLoginRequestUrl:  false,
  },
  cache: {
    cacheLocation:          "sessionStorage",  // don't use localStorage — XSS safer
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        if (import.meta.env.DEV) console.debug("[MSAL]", message);
      },
    },
  },
};

/** Scopes requested on initial login. */
export const loginRequest = {
  scopes: ["openid", "profile", "email", "User.Read"],
};

/** Scopes for Crown API calls (if using on-behalf-of or custom scope). */
export const apiRequest = {
  scopes: [
    import.meta.env.VITE_AAD_API_SCOPE || "User.Read",
  ],
};
