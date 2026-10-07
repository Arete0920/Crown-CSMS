import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import CrownLogo from "../components/brand/CrownLogo";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
const DEMO_SCHOOL = import.meta.env.VITE_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const IS_SANDBOX = Boolean(import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1");
const IS_WIZARD_CERTIFICATION = import.meta.env.VITE_WIZARD_CERTIFICATION === "1";
const ENABLE_SANDBOX_STUDENT = import.meta.env.VITE_SANDBOX_ENABLE_STUDENT !== "0";
const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || "support@crown2026.local";
const HERITAGE_SCHOOL_KEY = "heritage-core";
const HERITAGE_SCHOOL_NAME = "Heritage Christian Academy";

function apiUrl(path) {
  if (path.startsWith("http")) return path;
  return `${API_BASE}${path}`;
}

function inviteIdFromUrl() {
  try {
    return new URL(globalThis.location.href).searchParams.get("invite") || "";
  } catch {
    return "";
  }
}

const SANDBOX_ROLES = [
  { value: "school_admin", label: "School Admin", route: "/school-admin-dashboard" },
  ...(IS_WIZARD_CERTIFICATION ? [{ value: "admin", label: "School Admin", route: "/school-admin-dashboard" }] : []),
  { value: "admissions_director", label: "Admissions Director", route: "/admissions-dashboard" },
  { value: "finance_director", label: "Finance Director", route: "/finance" },
  { value: "teacher", label: "Teacher", route: "/teacher" },
  { value: "parent", label: "Parent", route: "/parent" },
  ...(ENABLE_SANDBOX_STUDENT ? [{ value: "student", label: "Student/Learner", route: "/student" }] : []),
  { value: "board", label: "School Board", route: "/board" },
];

const PROD_ROLES = [
  { value: "head_of_school", label: "Head of School", route: "/admin" },
  { value: "finance_director", label: "Finance Director", route: "/finance" },
  { value: "admissions_director", label: "Admissions Director", route: "/admissions-dashboard" },
  { value: "teacher", label: "Teacher", route: "/teacher" },
  { value: "parent", label: "Parent", route: "/parent" },
  { value: "student", label: "Student/Learner", route: "/student" },
];

function fallbackSandboxSchools() {
  return [{ id: DEMO_SCHOOL, name: HERITAGE_SCHOOL_NAME, schoolKey: HERITAGE_SCHOOL_KEY }];
}

function buildSchoolList(manifestSchools, sandboxMode) {
  if (sandboxMode) {
    return fallbackSandboxSchools();
  }

  const normalizedManifest = manifestSchools
    .map((school) => ({
      id: school?.id || school?.school_id,
      name: school?.name || school?.school_name,
    }))
    .filter((school) => school.id && school.name);

  return normalizedManifest.length > 0
    ? normalizedManifest
    : [{ id: DEMO_SCHOOL, name: HERITAGE_SCHOOL_NAME }];
}

function normalizeRoleList(payload, selectedRole) {
  const rawRoles = [
    selectedRole,
    payload?.role,
    payload?.primaryRole,
    payload?.role_code,
    payload?.roleCode,
    ...(Array.isArray(payload?.roles) ? payload.roles : []),
    ...(Array.isArray(payload?.userRoles) ? payload.userRoles : []),
  ];

  return [...new Set(rawRoles
    .map((entry) => {
      if (typeof entry === "string") return entry;
      return entry?.code || entry?.role || entry?.name || entry?.slug || entry?.value;
    })
    .filter(Boolean))];
}

function buildSessionUser(payload, role, selectedSchoolId, email) {
  const schoolId = payload?.school_id || payload?.schoolId || payload?.school?.id || selectedSchoolId || DEMO_SCHOOL;
  const roles = normalizeRoleList(payload, role.value);
  const primaryRole = roles[0] || role.value;

  return {
    ...(payload?.user && typeof payload.user === "object" ? payload.user : {}),
    ...(payload && typeof payload === "object" ? payload : {}),
    email: payload?.email || payload?.user?.email || email,
    username: payload?.username || payload?.user?.username || payload?.email || payload?.user?.email || email,
    role: primaryRole,
    primaryRole,
    roles,
    school_id: schoolId,
    schoolId,
  };
}

function persistAuthenticatedSession(payload, role, selectedSchoolId, email) {
  const access = payload?.access || payload?.token || "";
  const refresh = payload?.refresh || "";
  const currentUser = buildSessionUser(payload, role, selectedSchoolId, email);
  const schoolId = currentUser.school_id || selectedSchoolId || DEMO_SCHOOL;
  const serializedUser = JSON.stringify(currentUser);
  const serializedRoles = JSON.stringify(currentUser.roles || [role.value]);

  sessionStorage.setItem("crown.jwt.access", access);
  sessionStorage.setItem("crown.jwt.refresh", refresh);
  sessionStorage.setItem("crown.school.id", schoolId);
  sessionStorage.setItem("crown.role", role.value);
  sessionStorage.setItem("crown.active.role", role.value);
  sessionStorage.setItem("crown_user", serializedUser);
  sessionStorage.setItem("crown_current_user", serializedUser);
  sessionStorage.setItem("crown_user_roles", serializedRoles);

  // Persistent storage is limited to non-secret UI context. Bearer tokens and
  // authenticated-user payloads stay in sessionStorage so closing the tab drops them.
  localStorage.removeItem("crown.jwt.access");
  localStorage.removeItem("crown.jwt.refresh");
  localStorage.removeItem("crown_auth_token");
  localStorage.removeItem("access_token");
  localStorage.removeItem("crown_auth");
  localStorage.removeItem("crown_user");
  localStorage.removeItem("crown_current_user");
  localStorage.removeItem("crown_user_roles");
  localStorage.removeItem("crown.role");
  localStorage.removeItem("crown.active.role");
  localStorage.setItem("crown.school.id", schoolId);

  if (IS_SANDBOX) {
    localStorage.setItem("crown.role", role.value);
    localStorage.setItem("crown.active.role", role.value);
    localStorage.setItem("crown.demo.role", role.value);
  } else {
    localStorage.removeItem("crown.demo.role");
  }
}

async function fetchSchools(sandboxMode) {
  if (sandboxMode) {
    return fallbackSandboxSchools();
  }

  try {
    const response = await axios.get("/demo/schools_manifest.json");
    const manifestSchools = Array.isArray(response.data?.schools) ? response.data.schools : [];
    return buildSchoolList(manifestSchools, sandboxMode);
  } catch {
    return buildSchoolList([], sandboxMode);
  }
}

export default function LoginPage() {
  const roles = useMemo(() => (IS_SANDBOX ? SANDBOX_ROLES : PROD_ROLES), []);
  const [schools, setSchools] = useState(fallbackSandboxSchools());
  const [selectedSchoolId, setSelectedSchoolId] = useState(DEMO_SCHOOL);
  const [selectedRole, setSelectedRole] = useState(roles[0]?.value || "school_admin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    fetchSchools(IS_SANDBOX).then((loadedSchools) => {
      setSchools(loadedSchools);
      if (!loadedSchools.some((school) => school.id === selectedSchoolId)) {
        setSelectedSchoolId(loadedSchools[0]?.id || DEMO_SCHOOL);
      }
    });
  }, [selectedSchoolId]);

  async function startSandboxPreview(role) {
    const payload = {
      role: role.value,
      school: HERITAGE_SCHOOL_KEY,
      guidance: "guided",
      track: "school",
    };
    const inviteId = inviteIdFromUrl();
    if (inviteId) {
      payload.invite_id = inviteId;
    }

    const response = await globalThis.fetch(apiUrl("/api/v1/sandbox/session/"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      if (body?.code === "sandbox_invite_required") {
        throw new Error("Heritage sandbox preview is not currently open. Please use an approved sandbox link.");
      }
      throw new Error(body.detail || `Sandbox preview failed (${response.status})`);
    }

    const session = await response.json();
    persistAuthenticatedSession(
      session,
      role,
      session?.school_id || selectedSchoolId,
      session?.email || "heritage-sandbox-preview@crown.demo",
    );

    globalThis.location.href = session?.route || role.route;
  }

  async function handleSignIn(event) {
    event.preventDefault();
    if (isBusy) return;

    setError("");
    setIsBusy(true);

    const selectedRoleEntry = roles.find((entry) => entry.value === selectedRole) || roles[0];
    const role = IS_SANDBOX && selectedRoleEntry?.value === "admin"
      ? (SANDBOX_ROLES.find((entry) => entry.value === "school_admin") || selectedRoleEntry)
      : selectedRoleEntry;

    try {
      if (IS_SANDBOX) {
        await startSandboxPreview(role);
        return;
      }

      const username = email.trim();
      const pass = password;
      if (!username || !pass) {
        throw new Error("Email and password are required.");
      }
      const response = await globalThis.fetch(apiUrl("/api/v1/auth/token/"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password: pass }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Auth failed (${response.status})`);
      }

      const payload = await response.json();
      persistAuthenticatedSession(payload, role, selectedSchoolId, username);

      globalThis.location.href = role.route;
    } catch (authError) {
      setError(authError.message || (IS_SANDBOX ? "Sandbox preview failed." : "Login failed. Is the backend running?"));
      setIsBusy(false);
    }
  }

  return (
    <>
      <style>{`
        :root {
          --lp-navy-900: var(--crown-primary-deep, var(--crown-compat-color-2042bc3e08));
          --lp-navy-700: var(--crown-primary-strong, var(--crown-compat-color-135d678f70));
          --lp-slate-100: var(--crown-bg-soft, var(--crown-compat-color-d02714fbd1));
          --lp-slate-200: var(--crown-border, var(--crown-compat-color-b89dd2451e));
          --lp-slate-500: var(--crown-muted, var(--crown-compat-color-74d26b72f4));
          --lp-gold-500: var(--crown-gold, var(--crown-compat-color-e460033f2b));
          --lp-gold-100: var(--crown-gold-soft, var(--crown-compat-color-c4dcfe6c94));
          --lp-danger-100: var(--crown-danger-soft, var(--crown-compat-color-4b54505300));
          --lp-danger-600: var(--crown-danger, var(--crown-compat-color-b68a16e75c));
          --lp-white: var(--crown-surface, var(--crown-compat-color-f2074b6cef));
        }

        *, *::before, *::after { box-sizing: border-box; }

        .login-root {
          min-height: 100vh;
          display: grid;
          grid-template-columns: minmax(280px, 42%) minmax(320px, 58%);
          font-family: var(--crown-font);
          background: linear-gradient(150deg, var(--crown-compat-color-d02714fbd1) 0%, var(--crown-compat-color-2c1d554440) 70%);
          color: var(--crown-compat-color-effb26a3ee);
        }

        .login-brand {
          background: radial-gradient(130% 130% at 10% 20%, var(--crown-compat-color-550e1aa105) 0%, var(--lp-navy-900) 72%);
          color: var(--lp-white);
          padding: 42px 38px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          position: relative;
          overflow: hidden;
        }

        .login-brand::after {
          content: '';
          position: absolute;
          right: -120px;
          bottom: -120px;
          width: 300px;
          height: 300px;
          border-radius: 50%;
          background: radial-gradient(circle, var(--crown-compat-color-466b65c373) 0%, var(--crown-compat-color-0578810107) 72%);
          pointer-events: none;
        }

        .brand-top { position: relative; z-index: 1; }

        .brand-mark {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 30px;
        }

        .brand-mark .crown-logo-loginBrand {
          max-width: 240px;
          width: 100%;
        }

        .brand-mark .crown-brand-text-fallback,
        .brand-mark .crown-brand-text-fallback strong,
        .brand-mark .crown-brand-text-fallback span {
          color: var(--crown-compat-color-f2074b6cef);
        }

        .brand-title {
          font-family: var(--crown-font);
          font-weight: 600;
          font-size: 24px;
          line-height: 1;
        }

        .brand-subtitle {
          opacity: 0.78;
          font-size: 12px;
          letter-spacing: 0.2px;
        }

        .brand-heading {
          font-family: var(--crown-font);
          font-size: 33px;
          line-height: 1.2;
          margin: 0 0 12px;
        }

        .brand-trust {
          margin: 0 0 18px;
          color: var(--crown-compat-color-4dbf72a094);
          font-size: 15px;
          line-height: 1.5;
        }

        .brand-guidance {
          margin: 0 0 14px;
          color: var(--crown-compat-color-b287e65b63);
          font-size: 14px;
          line-height: 1.5;
        }

        .brand-bullets {
          margin: 0;
          padding-left: 18px;
          display: grid;
          gap: 8px;
          color: var(--crown-compat-color-ea1e459fee);
          font-size: 14px;
        }

        .brand-footer {
          position: relative;
          z-index: 1;
          margin-top: 24px;
          padding-top: 16px;
          border-top: 1px solid var(--crown-compat-color-5089217ef2);
          color: var(--crown-compat-color-58218d7102);
          font-size: 12px;
        }

        .login-panel {
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 34px 22px;
        }

        .login-card {
          width: 100%;
          max-width: 500px;
          background: var(--lp-white);
          border-radius: 16px;
          box-shadow: 0 10px 32px var(--crown-compat-color-e5630c697b);
          border: 1px solid var(--lp-slate-200);
          padding: 24px;
        }

        .sandbox-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border-radius: 999px;
          background: var(--crown-compat-color-166130d001);
          border: 1px solid var(--crown-compat-color-9d2fa2fa45);
          color: var(--lp-navy-700);
          padding: 5px 11px;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.2px;
          margin-bottom: 12px;
        }

        .login-title {
          margin: 0;
          font-family: var(--crown-font);
          font-size: 31px;
          color: var(--crown-compat-color-8e47de7f3c);
          line-height: 1.15;
        }

        .login-subtitle {
          margin: 8px 0 12px;
          color: var(--crown-compat-color-7691aaa644);
          font-size: 15px;
          line-height: 1.45;
        }

        .warning-banner {
          border: 1px solid var(--lp-gold-500);
          background: var(--lp-gold-100);
          color: var(--crown-compat-color-1588a009e3);
          padding: 10px 12px;
          border-radius: 10px;
          font-size: 13px;
          font-weight: 700;
          line-height: 1.45;
          margin-bottom: 14px;
        }

        .field-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 12px;
        }

        .field-label {
          display: block;
          margin-bottom: 5px;
          font-size: 13px;
          color: var(--crown-compat-color-0f64de779d);
          font-weight: 700;
        }

        .field-input,
        .field-select {
          width: 100%;
          border: 1px solid var(--crown-compat-color-17a67ab8c6) !important;
          border-radius: 9px;
          padding: 10px 11px;
          font-size: 14px;
          color: var(--crown-compat-color-58a558915f) !important;
          caret-color: var(--crown-compat-color-58a558915f) !important;
          -webkit-text-fill-color: var(--crown-compat-color-58a558915f) !important;
          background: var(--lp-white) !important;
          background-color: var(--lp-white) !important;
        }

        .field-input::placeholder {
          color: var(--crown-compat-color-7beae9beff) !important;
          -webkit-text-fill-color: var(--crown-compat-color-7beae9beff) !important;
          opacity: 1;
        }

        .field-input:focus,
        .field-select:focus,
        .btn-signin:focus,
        .btn-microsoft:focus {
          outline: 2px solid var(--crown-compat-color-8f251077d9);
          outline-offset: 2px;
          border-color: var(--crown-compat-color-2fcc0c461d);
        }

        .btn-signin {
          margin-top: 4px;
          width: 100%;
          border: 0;
          border-radius: 10px;
          background: linear-gradient(120deg, var(--lp-navy-900) 0%, var(--lp-navy-700) 100%);
          color: var(--crown-compat-color-f2074b6cef) !important;
          -webkit-text-fill-color: var(--crown-compat-color-f2074b6cef) !important;
          padding: 12px 14px;
          font-size: 15px;
          font-weight: 700;
          cursor: pointer;
        }

        .btn-signin:not([disabled]):hover {
          filter: brightness(1.03);
        }

        .btn-signin[disabled] {
          opacity: 0.65;
          cursor: wait;
        }

        .btn-microsoft {
          margin-top: 10px;
          width: 100%;
          border: 1px solid var(--crown-compat-color-80e0759046);
          border-radius: 10px;
          background: var(--crown-compat-color-f2074b6cef);
          color: var(--crown-compat-color-21b23e7ef3);
          padding: 10px 12px;
          font-size: 14px;
          font-weight: 700;
          cursor: pointer;
        }

        .error-banner {
          border: 1px solid var(--crown-compat-color-05f1c462d9);
          background: var(--lp-danger-100);
          color: var(--lp-danger-600);
          border-radius: 9px;
          padding: 9px 11px;
          font-size: 13px;
          font-weight: 700;
        }

        .support-note {
          margin: 10px 0 2px;
          color: var(--lp-slate-500);
          font-size: 12px;
          line-height: 1.5;
        }

        .product-footer {
          margin: 13px 0 0;
          color: var(--crown-compat-color-fff712ee45);
          font-size: 12px;
          text-align: center;
          font-weight: 600;
        }

        @media (max-width: 980px) {
          .login-root {
            grid-template-columns: 1fr;
          }

          .login-brand {
            padding: 28px 22px;
          }

          .login-panel {
            align-items: flex-start;
            padding-top: 16px;
          }
        }

        @media (max-width: 520px) {
          .login-card {
            padding: 18px;
          }

          .login-title {
            font-size: 27px;
          }

          .brand-heading {
            font-size: 27px;
          }
        }
      `}</style>

      <main className="login-root">
        <section className="login-brand" aria-label="Crown guidance">
          <div className="brand-top">
            <div className="brand-mark">
              <CrownLogo placement="loginBrand" />
              <span className="crown-brand-sr-only">
                <span>CROWN</span>
                <span>Christian School Management Solution</span>
              </span>
            </div>

            <h1 className="brand-heading">{IS_SANDBOX ? "CROWN Heritage Preview" : "CROWN Access"}</h1>
            <p className="brand-trust">
              {IS_SANDBOX
                ? "A controlled no-login preview of Heritage Christian Academy demo workflows."
                : "A calm and secure sign-in experience for school teams and families."}
            </p>
            <p className="brand-guidance">
              {IS_SANDBOX
                ? "Choose a role and continue into demo-only CROWN workflows. No password is required for this preview."
                : "Choose your school, choose your role, and continue with the correct context before entering any records."}
            </p>
            <ul className="brand-bullets">
              <li>{IS_SANDBOX ? "Heritage Christian Academy is the only approved sandbox school." : "Clear school and role context on every login."}</li>
              <li>Sandbox-safe workflows for tester and operator training.</li>
              <li>Permission-scoped access for each stakeholder role.</li>
            </ul>
          </div>

          <p className="brand-footer">CROWN - Christian School Management Solution</p>
        </section>

        <section className="login-panel" aria-label={IS_SANDBOX ? "Heritage sandbox preview panel" : "Login form panel"}>
          <form className="login-card" onSubmit={handleSignIn}>
            {IS_SANDBOX && <div className="sandbox-badge">Heritage Sandbox Preview</div>}

            <h2 className="login-title">{IS_SANDBOX ? "Continue to Preview" : "Sign In"}</h2>
            <p className="login-subtitle">
              {IS_SANDBOX
                ? "Heritage Christian Academy is the approved demo school. Select a role to enter the no-login sandbox preview."
                : "Use your authorized role and account to access CROWN."}
            </p>

            {IS_SANDBOX && (
              <div className="warning-banner">Use demo data only. Do not enter real school records.</div>
            )}

            {error && <div className="error-banner" role="alert">{error}</div>}

            <div className="field-grid">
              <div>
                <label className="field-label" htmlFor="login-school">School</label>
                <select
                  id="login-school"
                  className="field-select"
                  value={selectedSchoolId}
                  onChange={(event) => setSelectedSchoolId(event.target.value)}
                  disabled={IS_SANDBOX}
                >
                  {schools.map((school) => (
                    <option key={school.id} value={school.id}>{school.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="field-label" htmlFor="login-role">Role</label>
                <select
                  id="login-role"
                  className="field-select"
                  value={selectedRole}
                  onChange={(event) => setSelectedRole(event.target.value)}
                >
                  {roles.map((role) => (
                    <option key={role.value} value={role.value}>{role.label}</option>
                  ))}
                </select>
              </div>

              {!IS_SANDBOX && (
                <>
                  <div>
                    <label className="field-label" htmlFor="login-email">Email</label>
                    <input
                      id="login-email"
                      className="field-input"
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                      autoComplete="username"
                      placeholder="name@school.org"
                      required
                    />
                  </div>

                  <div>
                    <label className="field-label" htmlFor="login-password">Password</label>
                    <input
                      id="login-password"
                      className="field-input"
                      type="password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                      autoComplete="current-password"
                      placeholder="enter your password"
                      required
                    />
                  </div>
                </>
              )}

              <button type="submit" className="btn-signin" disabled={isBusy}>
                {isBusy ? (IS_SANDBOX ? "Opening preview..." : "Signing in...") : (IS_SANDBOX ? "Continue to Heritage Preview" : "Sign In")}
              </button>

              {!IS_SANDBOX && (
                <button
                  type="button"
                  className="btn-microsoft"
                  onClick={() => {
                    globalThis.location.href = API_BASE + "/auth/microsoft/login/";
                  }}
                >
                  Continue with Microsoft 365
                </button>
              )}
            </div>

            <p className="support-note">
              {IS_SANDBOX
                ? "This preview contains demo data only and does not expose real school records."
                : <>Need help? Contact your school administrator or {SUPPORT_EMAIL}.</>}
            </p>
            <p className="product-footer">CROWN - Christian School Management Solution</p>
          </form>
        </section>
      </main>
    </>
  );
}