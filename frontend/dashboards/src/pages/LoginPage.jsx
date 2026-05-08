import { useEffect, useMemo, useState } from "react";
import axios from "axios";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
const DEMO_SCHOOL = import.meta.env.VITE_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const IS_SANDBOX = Boolean(import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1");
const ENABLE_SANDBOX_STUDENT = import.meta.env.VITE_SANDBOX_ENABLE_STUDENT !== "0";
const SANDBOX_DEFAULT_EMAIL = "admin@heritage.example.org";
const SANDBOX_DEFAULT_PASS = import.meta.env.VITE_DEMO_PASS || "CrownDemo!2026";
const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || "support@crown2026.local";

const SANDBOX_ROLES = [
  { value: "school_admin", label: "School Admin", route: "/school-admin-dashboard" },
  { value: "teacher", label: "Teacher", route: "/teacher" },
  { value: "parent", label: "Parent", route: "/parent" },
  ...(ENABLE_SANDBOX_STUDENT ? [{ value: "student", label: "Student/Learner", route: "/student" }] : []),
];

const PROD_ROLES = [
  { value: "head_of_school", label: "Head of School", route: "/admin" },
  { value: "finance_director", label: "Finance Director", route: "/finance" },
  { value: "admissions_director", label: "Admissions Director", route: "/admissions-dashboard" },
  { value: "teacher", label: "Teacher", route: "/teacher" },
  { value: "parent", label: "Parent", route: "/parent" },
  { value: "student", label: "Student/Learner", route: "/student" },
];

const SANDBOX_SCHOOL_NAMES = [
  "Heritage Christian Academy",
  "Harvest Christian School",
  "Faith Christian Academy",
  "Calvary Christian School",
  "St. Anne Christian Academy",
  "Grace Covenant School",
  "Providence Christian Academy",
  "Trinity Classical School",
  "Redeemer Christian School",
  "Cornerstone Christian Academy",
  "New Hope Christian School",
  "Legacy Christian Academy",
  "Emmanuel Christian School",
  "King's Way Christian Academy",
  "Bethel Christian School",
  "Veritas Christian Academy",
  "Crossroads Christian School",
  "Shepherd's Gate Academy",
  "Lighthouse Christian School",
  "Covenant Preparatory School",
];

function normalizeSchoolId(name, index) {
  if (index === 0) return DEMO_SCHOOL;
  return `sandbox-school-${name.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-").replaceAll(/^-+|-+$/g, "")}`;
}

function fallbackSandboxSchools() {
  return SANDBOX_SCHOOL_NAMES.map((name, index) => ({
    id: normalizeSchoolId(name, index),
    name,
  }));
}

function buildSchoolList(manifestSchools, sandboxMode) {
  const normalizedManifest = manifestSchools
    .map((school) => ({
      id: school?.id || school?.school_id,
      name: school?.name || school?.school_name,
    }))
    .filter((school) => school.id && school.name);

  if (!sandboxMode) {
    return normalizedManifest.length > 0
      ? normalizedManifest
      : [{ id: DEMO_SCHOOL, name: "Heritage Christian Academy" }];
  }

  const required = fallbackSandboxSchools();
  const byName = new Map(normalizedManifest.map((school) => [school.name.toLowerCase(), school]));
  return required.map((school) => {
    const existing = byName.get(school.name.toLowerCase());
    return existing ? { ...existing } : school;
  });
}

async function fetchSandboxCredentials() {
  try {
    const response = await axios.get("/demo/heritage_demo_credentials.json");
    const personas = Array.isArray(response.data?.required_personas) ? response.data.required_personas : [];
    const adminPersona = personas.find((persona) => persona.key === "school_admin") || personas[0];
    return {
      email: adminPersona?.email || SANDBOX_DEFAULT_EMAIL,
      password: SANDBOX_DEFAULT_PASS,
    };
  } catch {
    return {
      email: SANDBOX_DEFAULT_EMAIL,
      password: SANDBOX_DEFAULT_PASS,
    };
  }
}

async function fetchSchools(sandboxMode) {
  try {
    const response = await axios.get("/demo/schools_manifest.json");
    const manifestSchools = Array.isArray(response.data?.schools) ? response.data.schools : [];
    return buildSchoolList(manifestSchools, sandboxMode);
  } catch {
    return buildSchoolList([], sandboxMode);
  }
}

function CrownMark() {
  return (
    <svg viewBox="0 0 120 92" width="42" height="32" aria-hidden="true">
      <defs>
        <linearGradient id="crownFill" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.88)" />
        </linearGradient>
      </defs>
      <rect x="7" y="66" width="106" height="18" rx="5" fill="url(#crownFill)" />
      <polygon points="7,66 7,30 35,52 60,5 85,52 113,30 113,66" fill="url(#crownFill)" />
      <rect x="7" y="68" width="106" height="3" rx="1.5" fill="#C6A54A" />
      <circle cx="60" cy="5" r="8" fill="#C6A54A" />
      <circle cx="7" cy="30" r="6" fill="#C6A54A" />
      <circle cx="113" cy="30" r="6" fill="#C6A54A" />
    </svg>
  );
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

  useEffect(() => {
    if (!IS_SANDBOX) return;
    fetchSandboxCredentials().then((credentials) => {
      setEmail(credentials.email);
      setPassword(credentials.password);
    });
  }, []);

  function fillSandboxCredentials() {
    setEmail(SANDBOX_DEFAULT_EMAIL);
    setPassword(SANDBOX_DEFAULT_PASS);
  }

  async function handleSignIn(event) {
    event.preventDefault();
    if (isBusy) return;

    setError("");
    setIsBusy(true);

    const role = roles.find((entry) => entry.value === selectedRole) || roles[0];

    try {
      const username = IS_SANDBOX ? email : (email || "demo@crown.example.org");
        const pass = IS_SANDBOX ? password : (password || "demo-password");
      const response = await globalThis.fetch("/api/v1/auth/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password: pass }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Auth failed (${response.status})`);
      }

      const payload = await response.json();
      sessionStorage.setItem("crown.jwt.access", payload.access);
      sessionStorage.setItem("crown.school.id", payload.school_id || selectedSchoolId || DEMO_SCHOOL);
      sessionStorage.setItem("crown.role", role.value);
      localStorage.setItem("crown.role", role.value);
      if (IS_SANDBOX) {
        localStorage.setItem("crown.demo.role", role.value);
      }

      globalThis.location.href = role.route;
    } catch (authError) {
      setError(authError.message || "Login failed. Is the backend running?");
      setIsBusy(false);
    }
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=Spectral:wght@500;600&display=swap');

        :root {
          --lp-navy-900: #0C223C;
          --lp-navy-700: #183A63;
          --lp-slate-100: #F4F7FB;
          --lp-slate-200: #E3EAF3;
          --lp-slate-500: #5B6E83;
          --lp-gold-500: #C6A54A;
          --lp-gold-100: #FBF6E8;
          --lp-danger-100: #FEF2F2;
          --lp-danger-600: #B42318;
          --lp-white: #FFFFFF;
        }

        *, *::before, *::after { box-sizing: border-box; }

        .login-root {
          min-height: 100vh;
          display: grid;
          grid-template-columns: minmax(280px, 42%) minmax(320px, 58%);
          font-family: 'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
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

        .brand-title {
          font-family: 'Spectral', Georgia, serif;
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
          font-family: 'Spectral', Georgia, serif;
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
          font-family: 'Spectral', Georgia, serif;
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
        .btn-fill:focus,
        .btn-microsoft:focus {
          outline: 2px solid rgba(26, 111, 168, 0.35);
          outline-offset: 2px;
          border-color: #1A6FA8;
        }

        .inline-row {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 8px;
          align-items: end;
        }

        .btn-fill {
          border: 1px solid #B8CBE0;
          background: #F2F7FD;
          color: #1F4467;
          border-radius: 9px;
          padding: 10px 12px;
          font-weight: 700;
          cursor: pointer;
          white-space: nowrap;
        }

        .btn-signin {
          margin-top: 4px;
          width: 100%;
          border: 0;
          border-radius: 10px;
          background: linear-gradient(120deg, #12345A 0%, #1E4A7A 100%);
          color: #FFFFFF;
          padding: 12px 14px;
          font-size: 15px;
          font-weight: 700;
          cursor: pointer;
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

          .inline-row {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <main className="login-root">
        <section className="login-brand" aria-label="Crown guidance">
          <div className="brand-top">
            <div className="brand-mark">
              <CrownMark />
              <div>
                <div className="brand-title">CROWN</div>
                <div className="brand-subtitle">Christian School Management Solution</div>
              </div>
            </div>

            <h1 className="brand-heading">{IS_SANDBOX ? "CROWN Sandbox Access" : "CROWN Access"}</h1>
            <p className="brand-trust">
              A calm and secure sign-in experience for school teams and families.
            </p>
            <p className="brand-guidance">
              Choose your school, choose your role, and continue with the correct context before entering any records.
            </p>
            <ul className="brand-bullets">
              <li>Clear school and role context on every login.</li>
              <li>Sandbox-safe workflows for tester and operator training.</li>
              <li>Permission-scoped access for each stakeholder role.</li>
            </ul>
          </div>

          <p className="brand-footer">CROWN - Christian School Management Solution</p>
        </section>

        <section className="login-panel" aria-label="Login form panel">
          <form className="login-card" onSubmit={handleSignIn}>
            {IS_SANDBOX && <div className="sandbox-badge">Sandbox Environment</div>}

            <h2 className="login-title">Sign In</h2>
            <p className="login-subtitle">
              {IS_SANDBOX
                ? "Choose your sandbox school and role, then continue with sandbox credentials."
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

              <div>
                <label className="field-label" htmlFor="login-email">Email</label>
                <input
                  id="login-email"
                  className="field-input"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="username"
                  placeholder={IS_SANDBOX ? "sandbox operator email" : "name@school.org"}
                  required
                />
              </div>

              <div>
                <label className="field-label" htmlFor="login-password">Password</label>
                <div className="inline-row">
                  <input
                    id="login-password"
                    className="field-input"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                    placeholder={IS_SANDBOX ? "sandbox password" : "enter your password"}
                    required
                  />
                  {IS_SANDBOX && (
                    <button type="button" className="btn-fill" onClick={fillSandboxCredentials}>
                      Use Sandbox Credentials
                    </button>
                  )}
                </div>
              </div>

              <button type="submit" className="btn-signin" disabled={isBusy}>
                {isBusy ? "Signing in..." : "Sign In"}
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
              Need help? Contact your school administrator or {SUPPORT_EMAIL}.
            </p>
            <p className="product-footer">CROWN - Christian School Management Solution</p>
          </form>
        </section>
      </main>
    </>
  );
}

