import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import CrownLogo from "../components/brand/CrownLogo";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
const DEMO_SCHOOL = import.meta.env.VITE_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const IS_SANDBOX = Boolean(import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1");
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

  localStorage.setItem("crown.jwt.access", access);
  localStorage.setItem("crown.school.id", schoolId);
  localStorage.setItem("crown.role", role.value);
  localStorage.setItem("crown.active.role", role.value);
  localStorage.setItem("crown_user", serializedUser);
  localStorage.setItem("crown_current_user", serializedUser);
  localStorage.setItem("crown_user_roles", serializedRoles);

  if (IS_SANDBOX) {
    localStorage.setItem("crown.demo.role", role.value);
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

    const role = roles.find((entry) => entry.value === selectedRole) || roles[0];

    try {
      if (IS_SANDBOX) {
        await startSandboxPreview(role);
        return;
      }

      const username = email || "demo@crown.example.org";
      const pass = password || "demo-password";
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
          --lp-navy-900: var(--crown-primary-deep, #173F91);
          --lp-navy-700: var(--crown-primary-strong, #1E4FAF);
          --lp-slate-100: var(--crown-bg-soft, #EFF4FB);
          --lp-slate-200: var(--crown-border, #D6E3F5);
          --lp-slate-500: var(--crown-muted, #42566E);
          --lp-gold-500: var(--crown-gold, #C28A24);
          --lp-gold-100: var(--crown-gold-soft, #FFF3D6);
          --lp-danger-100: var(--crown-danger-soft, #FEE2E2);
          --lp-danger-600: var(--crown-danger, #B4232C);
          --lp-white: var(--crown-surface, #FFFFFF);
        }

        *, *::before, *::after { box-sizing: border-box; }

        .login-root {
          min-height: 100vh;
          display: grid;
          grid-template-columns: minmax(280px, 42%) minmax(320px, 58%);
          font-family: var(--crown-font);
          background: linear-gradient(150deg, #EFF4FB 0%, #F8FBFF 70%);
          color: #0E1D30;
        }

        .login-brand {
          background: radial-gradient(130% 130% at 10% 20%, #1E4A7A 0%, var(--lp-navy-900) 72%);
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
          background: radial-gradient(circle, rgba(198,165,74,0.2) 0%, rgba(198,165,74,0) 72%);
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
          color: #FFFFFF;
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
          color: rgba(255,255,255,0.88);
          font-size: 15px;
          line-height: 1.5;
        }

        .brand-guidance {
          margin: 0 0 14px;
          color: rgba(255,255,255,0.72);
          font-size: 14px;
          line-height: 1.5;
        }

        .brand-bullets {
          margin: 0;
          padding-left: 18px;
          display: grid;
          gap: 8px;
          color: rgba(255,255,255,0.9);
          font-size: 14px;
        }

        .brand-footer {
          position: relative;
          z-index: 1;
          margin-top: 24px;
          padding-top: 16px;
          border-top: 1px solid rgba(255,255,255,0.15);
          color: rgba(255,255,255,0.82);
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
          box-shadow: 0 10px 32px rgba(11, 29, 49, 0.14);
          border: 1px solid var(--lp-slate-200);
          padding: 24px;
        }

        .sandbox-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border-radius: 999px;
          background: #EDF4FF;
          border: 1px solid #C8DAF5;
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
          color: #112A46;
          line-height: 1.15;
        }

        .login-subtitle {
          margin: 8px 0 12px;
          color: #304A63;
          font-size: 15px;
          line-height: 1.45;
        }

        .warning-banner {
          border: 1px solid var(--lp-gold-500);
          background: var(--lp-gold-100);
          color: #7A5317;
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
          color: #1C3550;
          font-weight: 700;
        }

        .field-input,
        .field-select {
          width: 100%;
          border: 1px solid #CBD8E6 !important;
          border-radius: 9px;
          padding: 10px 11px;
          font-size: 14px;
          color: #102843 !important;
          caret-color: #102843 !important;
          -webkit-text-fill-color: #102843 !important;
          background: var(--lp-white) !important;
          background-color: var(--lp-white) !important;
        }

        .field-input::placeholder {
          color: #5B6E83 !important;
          -webkit-text-fill-color: #5B6E83 !important;
          opacity: 1;
        }

        .field-input:focus,
        .field-select:focus,
        .btn-signin:focus,
        .btn-microsoft:focus {
          outline: 2px solid rgba(26, 111, 168, 0.35);
          outline-offset: 2px;
          border-color: #1A6FA8;
        }

        .btn-signin {
          margin-top: 4px;
          width: 100%;
          border: 0;
          border-radius: 10px;
          background: linear-gradient(120deg, var(--lp-navy-900) 0%, var(--lp-navy-700) 100%);
          color: #FFFFFF !important;
          -webkit-text-fill-color: #FFFFFF !important;
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
          border: 1px solid #C9D7E6;
          border-radius: 10px;
          background: #FFFFFF;
          color: #183556;
          padding: 10px 12px;
          font-size: 14px;
          font-weight: 700;
          cursor: pointer;
        }

        .error-banner {
          border: 1px solid #F7B7B7;
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
          color: #3B526A;
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
