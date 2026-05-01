/**
 * demoAutoLogin.ts
 * Demo-only auto login for investor presentations.
 * Hard-gated to VITE_DEMO_MODE=1 && VITE_DEMO_AUTO_LOGIN=1.
 * NEVER runs in production.
 */

export async function ensureDemoAutoLogin({
  apiBase,
  username,
  password,
  schoolId,
  tokenKey,
  schoolKey,
  role,
  roleKey,
}: {
  apiBase: string;
  username: string;
  password: string;
  schoolId: string;
  tokenKey: string;
  schoolKey: string;
  role: string;
  roleKey: string;
}): Promise<boolean> {
  const isDemoMode = import.meta.env.VITE_DEMO_MODE === "1";
  const autoLogin = import.meta.env.VITE_DEMO_AUTO_LOGIN === "1";
  if (!isDemoMode || !autoLogin) return false;

  const existing = sessionStorage.getItem(tokenKey);
  if (existing && existing.length > 20) return false; // already logged in

  const resp = await fetch(`${apiBase}/api/v1/auth/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Demo auto-login failed (${resp.status}): ${text}`);
  }

  const data = await resp.json();
  if (!data?.access) throw new Error("Demo auto-login failed: missing access token");

  // Write to both sessionStorage (primary) and localStorage (fallback for tab reopen)
  sessionStorage.setItem(tokenKey, data.access);
  localStorage.setItem(tokenKey, data.access);
  sessionStorage.setItem(schoolKey, schoolId);
  localStorage.setItem(schoolKey, schoolId);

  // Set role so RoleRouteGuard and RequirePermission resolve correctly in demo mode
  sessionStorage.setItem(roleKey, role);
  localStorage.setItem(roleKey, role);
  localStorage.setItem("crown.demo.role", role);
  localStorage.setItem("crown_user", JSON.stringify({
    username,
    role,
    school_id: schoolId,
  }));
  return true;
}
