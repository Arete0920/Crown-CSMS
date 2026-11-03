import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import {
  clearBrowserAuthState, jwtLogin, setAccessToken,
} from "../utils/authClient.js";

/**
 * Separate fictional SGO identity entry point. The protected Heritage sandbox
 * login is role-session based and must never accept generic SGO credentials.
 */
export default function JirehSGOLoginPage() {
  const local = import.meta.env.VITE_LOCAL_DEMO === "1";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function signIn(event) {
    event.preventDefault();
    if (!local || busy || !username.trim() || !password) return;
    setBusy(true);
    setError("");
    try {
      // Existing SimpleJWT authentication; no new credential or anonymous API.
      const session = await jwtLogin({ username: username.trim(), password });
      if (!session?.access) throw new Error("Invalid token response.");
      // No school/role identity or parent token from another session may carry
      // into this standalone, per-program SGO grant authorization domain.
      clearBrowserAuthState();
      setAccessToken(session.access);
      setPassword("");
      globalThis.location.assign("/jireh-sgo/intake");
    } catch {
      setPassword("");
      setError("Fictional SGO account authentication failed. Check the private local credentials file.");
      setBusy(false);
    }
  }

  return <CrownLayout navigationScope="standalone"
    title="Jireh SGO | Local Fictional Sign-In"
    subtitle="Independent partner programs — synthetic accounts only">
    <p>This local sign-in uses CROWN's existing authenticated JWT service.
      It does not grant access to another partner SGO or school.</p>
    {!local && <p role="alert">Fictional SGO sign-in is unavailable outside the isolated local demonstration.</p>}
    {local && <form onSubmit={signIn} style={{
      maxWidth: 460, border: "1px solid var(--crown-border)",
      borderRadius: 8, padding: "1rem", background: "var(--crown-surface)",
    }}>
      <p>Use the fictional family, processor, or partner account credentials stored locally
        in <code>.local-backups/heritage-demo/sgo-credentials.txt</code>.</p>
      <p><label htmlFor="sgo-username">Synthetic account username</label></p>
      <input id="sgo-username" type="text" autoComplete="username" required
        value={username} onChange={(event) => setUsername(event.target.value)}
        style={{ maxWidth: "100%", width: "100%" }} />
      <p><label htmlFor="sgo-password">Synthetic account password</label></p>
      <input id="sgo-password" type="password" autoComplete="current-password" required
        value={password} onChange={(event) => setPassword(event.target.value)}
        style={{ maxWidth: "100%", width: "100%" }} />
      {error && <p role="alert">{error}</p>}
      <p><button type="submit" disabled={busy || !username.trim() || !password}>
        {busy ? "Signing in…" : "Sign in to fictional SGO"}
      </button></p>
      <p><a href="/jireh-sgo/intake">Return to fictional intake</a></p>
    </form>}
  </CrownLayout>;
}
