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
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.2px;
          padding: 4px 10px;
          margin-bottom: 12px;
        }

        .login-card h1 {
          margin: 0 0 6px;
          font-family: var(--crown-font);
          color: var(--lp-navy-900);
          font-size: 24px;
        }

        .login-card p {
          margin: 0 0 18px;
          color: var(--lp-slate-500);
          font-size: 13px;
        }

        .form-group { margin-bottom: 14px; }
        .form-group label {
          display: block;
          font-size: 12px;
          font-weight: 700;
          color: var(--lp-navy-900);
          margin-bottom: 6px;
        }

        .form-group input,
        .form-group select {
          width: 100%;
          padding: 10px 12px;
          border: 1px solid var(--lp-slate-200);
          border-radius: 8px;
          background: var(--lp-white);
          color: var(--lp-navy-900);
          font-size: 14px;
          outline: none;
        }

        .form-group input:focus,
        .form-group select:focus {
          border-color: var(--lp-gold-500);
          box-shadow: 0 0 0 3px var(--lp-gold-100);
        }

        .error {
          margin: 0 0 14px;
          padding: 9px 10px;
          border-radius: 8px;
          background: var(--lp-danger-100);
          color: var(--lp-danger-600);
          font-size: 12px;
        }

        .login-actions {
          margin-top: 8px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .login-btn {
          border: 0;
          border-radius: 8px;
          background: var(--lp-navy-900);
          color: var(--lp-white);
          padding: 10px 16px;
          font-size: 13px;
          font-weight: 700;
          cursor: pointer;
        }

        .login-btn:hover { background: var(--lp-navy-700); }
        .login-btn:disabled { opacity: 0.65; cursor: wait; }

        .login-support {
          color: var(--lp-slate-500);
          font-size: 11px;
        }

        .login-support a {
          color: var(--lp-navy-700);
          text-decoration: none;
          font-weight: 600;
        }

        .login-meta {
          margin-top: 18px;
          padding-top: 12px;
          border-top: 1px solid var(--lp-slate-200);
          display: flex;
          justify-content: space-between;
          gap: 12px;
          color: var(--lp-slate-500);
          font-size: 11px;
        }

        @media (max-width: 820px) {
          .login-root { grid-template-columns: 1fr; }
          .login-brand { min-height: 300px; padding: 28px 22px; }
          .brand-heading { font-size: 27px; }
          .login-panel { padding: 24px 14px; }
        }
      `}</style>

      <main className="login-root">
        <section className="login-brand" aria-label="CROWN introduction">
          <div className="brand-top">
            <div className="brand-mark">
              <CrownLogo variant="loginBrand" alt="CROWN Christian School Management Solution" />
            </div>
            <h2 className="brand-heading">{IS_SANDBOX ? "Explore a complete Christian-school workflow." : "Welcome back to CROWN."}</h2>
            <p className="brand-trust">
              {IS_SANDBOX
                ? "This preview uses synthetic Heritage Christian Academy data and cannot reach live school records."
                : "Manage academics, operations, finance, enrollment, and community workflows from one system."}
            </p>
            <p className="brand-guidance">
              {IS_SANDBOX
                ? "Choose a role, enter the guided workspace, and use the contextual walkthroughs to evaluate real operational flows."
                : "Use your school credentials to continue."}
            </p>
            <ul className="brand-bullets">
              <li>Role-aware dashboards and permissions</li>
              <li>Admissions, enrollment, academics, and operations</li>
              <li>Finance and family-facing workflows</li>
              <li>Christian-school mission and community context</li>
            </ul>
          </div>
          <div className="brand-footer">
            CROWN — Christian School Management Solution
          </div>
        </section>

        <section className="login-panel">
          <form className="login-card" onSubmit={handleSignIn}>
            {IS_SANDBOX ? <div className="sandbox-badge">HERITAGE SANDBOX</div> : null}
            <h1>{IS_SANDBOX ? "Choose a preview role" : "Sign in"}</h1>
            <p>{IS_SANDBOX ? "No password is required for approved Heritage preview sessions." : "Enter your school credentials."}</p>

            <div className="form-group">
              <label htmlFor="login-school">School</label>
              <select
                id="login-school"
                value={selectedSchoolId}
                onChange={(event) => setSelectedSchoolId(event.target.value)}
                disabled={IS_SANDBOX}
              >
                {schools.map((school) => (
                  <option key={school.id} value={school.id}>{school.name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="login-role">Role</label>
              <select
                id="login-role"
                value={selectedRole}
                onChange={(event) => setSelectedRole(event.target.value)}
              >
                {roles.map((role) => (
                  <option key={role.value} value={role.value}>{role.label}</option>
                ))}
              </select>
            </div>

            {!IS_SANDBOX ? (
              <>
                <div className="form-group">
                  <label htmlFor="login-email">Email or username</label>
                  <input id="login-email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="username" />
                </div>
                <div className="form-group">
                  <label htmlFor="login-password">Password</label>
                  <input id="login-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
                </div>
              </>
            ) : null}

            {error ? <div className="error" role="alert">{error}</div> : null}

            <div className="login-actions">
              <button className="login-btn" type="submit" disabled={isBusy}>
                {isBusy ? "Opening…" : IS_SANDBOX ? "Continue to Heritage preview" : "Sign in"}
              </button>
              <div className="login-support">
                Need help? <a href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
              </div>
            </div>

            <div className="login-meta">
              <span>{IS_SANDBOX ? "Synthetic data only" : "Secure school access"}</span>
              <span>© CROWN</span>
            </div>
          </form>
        </section>
      </main>
    </>
  );
}
