import { useState, useEffect } from "react";

/*  Config  */
const API_BASE    = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
const DEMO_USER = "demo@crown.example.org";
const DEMO_PASS = "DemoPassword2026!";
const DEMO_SCHOOL = import.meta.env.VITE_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
const IS_SANDBOX  = Boolean(import.meta.env.VITE_DEMO_MODE === "sandbox" || import.meta.env.VITE_SANDBOX_MODE === "1");
const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || "support@crown2026.example.org";

// Default sandbox credentials (fallback)
const SANDBOX_DEFAULT_EMAIL = "admin@heritage.example.org";
const SANDBOX_DEFAULT_PASS = import.meta.env.VITE_DEMO_PASS || "Crown2026!";

// Only show sandbox login in sandbox mode
const ROLES = IS_SANDBOX ? [
  { label: "School Sandbox", desc: "Login to your sandbox environment.", route: "/sandbox", color: "#0F2C4C" }
] : [
  { label: "Head of School",      desc: "School-wide oversight & executive KPIs",   route: "/admin",         color: "#0F2C4C" },
  { label: "Financial Aid",       desc: "Aid awards, applications & packaging",      route: "/financial-aid-dashboard", color: "#1C4E80" },
  { label: "Finance Director",    desc: "AR, billing, aging & collections",          route: "/finance",       color: "#1A6FA8" },
  { label: "Admissions Director", desc: "Pipeline, enrollment & yield analytics",   route: "/admissions-dashboard",    color: "#2E7D62" },
  { label: "Teacher",             desc: "Gradebook, attendance & curriculum",        route: "/teacher",       color: "#7A5C14" },
  { label: "Parent",              desc: "Student progress, grades & messages",       route: "/parent",        color: "#3D5A80" },
  { label: "Student",             desc: "Assignments, schedule & academics",         route: "/student",       color: "#1B6B4A" },
  { label: "Board Member",        desc: "Governance, financials & strategic data",  route: "/board",         color: "#5B3D8A" },
];

// Define constant for sandbox admin home
const SANDBOX_ADMIN_HOME = "/school-admin-dashboard";

/*  SVGs  */
function CrownSVG({ size = 52 }) {
  return (
    <svg viewBox="0 0 120 90" width={size} height={Math.round(size * 0.75)} aria-hidden="true">
      <defs>
        <linearGradient id="lpCg" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%"   stopColor="#ffffff" />
          <stop offset="100%" stopColor="rgba(255,255,255,0.88)" />
        </linearGradient>
      </defs>
      <rect x="6" y="64" width="108" height="20" rx="5" fill="url(#lpCg)" />
      <polygon points="6,64 6,28 35,52 60,4 85,52 114,28 114,64" fill="url(#lpCg)" />
      <rect x="6" y="66" width="108" height="3" rx="1.5" fill="#C6A54A" />
      <circle cx="60"  cy="4"  r="8"   fill="#C6A54A" />
      <circle cx="6"   cy="28" r="6.5" fill="#C6A54A" />
      <circle cx="114" cy="28" r="6.5" fill="#C6A54A" />
    </svg>
  );
}

function MsIcon() {
  return (
    <svg viewBox="0 0 21 21" width="17" height="17" aria-hidden="true" style={{ flexShrink: 0 }}>
      <rect x="0"  y="0"  width="10" height="10" fill="#f25022" />
      <rect x="11" y="0"  width="10" height="10" fill="#7fba00" />
      <rect x="0"  y="11" width="10" height="10" fill="#00a4ef" />
      <rect x="11" y="11" width="10" height="10" fill="#ffb900" />
    </svg>
  );
}

function Spin() {
  return (
    <span style={{
      display: "inline-block", width: 13, height: 13,
      border: "2px solid rgba(255,255,255,0.25)",
      borderTopColor: "#fff",
      borderRadius: "50%",
      animation: "lp-spin 0.6s linear infinite",
      flexShrink: 0,
    }} />
  );
}

// Further simplify RoleCard by extracting subcomponents
function RoleCard({ role, busy, onLogin }) {
  const isBusy = busy === role.label;
  const isDim = !!busy && !isBusy;
  const [hov, setHov] = useState(false);

  // Simplify buttonCursor logic
  const buttonCursor = (() => {
    if (isBusy) return "wait";
    if (isDim) return "default";
    return "pointer";
  })();

  const buttonStyle = {
    display: "flex",
    alignItems: "center",
    width: "100%",
    gap: 0,
    padding: 0,
    border: "1px solid",
    borderColor: hov && !busy ? role.color : "#E4ECF5",
    borderLeft: `3px solid ${role.color}`,
    borderRadius: "7px",
    background: hov && !busy ? "#F6F9FF" : "#FFFFFF",
    cursor: buttonCursor,
    opacity: isDim ? 0.28 : 1,
    outline: "none",
    fontFamily: "inherit",
    textAlign: "left",
    overflow: "hidden",
    boxShadow: hov && !busy
      ? "0 2px 14px rgba(15,44,76,0.1)"
      : "0 1px 3px rgba(15,44,76,0.04)",
    transform: hov && !busy ? "translateY(-1px)" : "none",
    transition: "all 0.13s ease",
  };

  return (
    <button
      onClick={() => onLogin(role)}
      disabled={!!busy}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={buttonStyle}
    >
      <RoleCardContent role={role} isBusy={isBusy} />
    </button>
  );
}

function RoleCardContent({ role, isBusy }) {
  return (
    <div style={{ flex: 1, padding: "10px 11px" }}>
      <div
        style={{
          fontWeight: 600,
          fontSize: "13px",
          color: "#0D1F35",
          lineHeight: 1.25,
          marginBottom: isBusy ? 0 : "2px",
        }}
      >
        {isBusy ? (
          <span
            style={{
              display: "flex",
              alignItems: "center",
              gap: 7,
              color: "#0D1F35",
            }}
          >
            <Spin />Signing in...
          </span>
        ) : (
          role.label
        )}
      </div>
      {!isBusy && (
        <div
          style={{
            fontWeight: 400,
            fontSize: "11px",
            color: "#7B93AC",
            lineHeight: 1.4,
          }}
        >
          {role.desc}
        </div>
      )}
    </div>
  );
}

// Replace fetch with axios for better error handling
import axios from "axios";

async function fetchSandboxCredentials() {
  try {
    const res = await axios.get("/demo/heritage_demo_credentials.json");
    const data = res.data;
    const persona = data.required_personas?.find(p => p.key === "school_admin") || data.required_personas?.[0];
    return {
      email: persona?.email || SANDBOX_DEFAULT_EMAIL,
      pass: SANDBOX_DEFAULT_PASS,
    };
  } catch {
    return {
      email: SANDBOX_DEFAULT_EMAIL,
      pass: SANDBOX_DEFAULT_PASS,
    };
  }
}

async function fetchSchoolOptions() {
  try {
    const res = await axios.get("/demo/schools_manifest.json");
    const schools = Array.isArray(res.data?.schools) ? res.data.schools : [];
    const normalized = schools
      .map((s) => ({
        id: s?.id || s?.school_id,
        name: s?.name || s?.school_name,
      }))
      .filter((s) => s.id && s.name);
    if (normalized.length > 0) return normalized;
  } catch {
    // Fallback to env/default school when manifest is unavailable.
  }
  return [{ id: DEMO_SCHOOL, name: "Heritage Christian Academy" }];
}

/*  Page  */
export default function LoginPage() {
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [sandboxEmail, setSandboxEmail] = useState(SANDBOX_DEFAULT_EMAIL);
  const [sandboxPass, setSandboxPass] = useState(SANDBOX_DEFAULT_PASS);
  const [schools, setSchools] = useState([{ id: DEMO_SCHOOL, name: "Heritage Christian Academy" }]);
  const [selectedSchoolId, setSelectedSchoolId] = useState(DEMO_SCHOOL);

  // Prefill sandbox credentials from JSON if in sandbox mode
  useEffect(() => {
    if (IS_SANDBOX) {
      fetchSandboxCredentials().then((credentials) => {
        setSandboxEmail(credentials.email);
        setSandboxPass(credentials.pass);
      }).catch(() => {
        setSandboxEmail(SANDBOX_DEFAULT_EMAIL);
        setSandboxPass(SANDBOX_DEFAULT_PASS);
      });
    }
  }, []);

  useEffect(() => {
    fetchSchoolOptions().then((items) => {
      setSchools(items);
      if (!items.some((s) => s.id === selectedSchoolId)) {
        setSelectedSchoolId(items[0]?.id || DEMO_SCHOOL);
      }
    }).catch(() => {
      setSchools([{ id: DEMO_SCHOOL, name: "Heritage Christian Academy" }]);
      setSelectedSchoolId(DEMO_SCHOOL);
    });
  }, []);

  async function login(role) {
    if (busy) return;
    setError("");
    setBusy(role.label);
    try {
      let access = null, schoolId = selectedSchoolId || DEMO_SCHOOL;
      let username = sandboxEmail;
      let password = sandboxPass;
      if (!IS_SANDBOX) {
        username = DEMO_USER;
        password = DEMO_PASS;
      }
      // Only allow sandbox login in sandbox mode
      const r = await globalThis.fetch("/api/v1/auth/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!r.ok) {
        const b = await r.json().catch(() => ({}));
        throw new Error(b.detail || `Auth failed (${r.status})`);
      }
      const d = await r.json();
      access = d.access;
      schoolId = d.school_id || selectedSchoolId || DEMO_SCHOOL;
      sessionStorage.setItem("crown.jwt.access", access);
      sessionStorage.setItem("crown.school.id", schoolId);

      // Redirect sandbox admins to the redesigned admin dashboard
      if (IS_SANDBOX && role.label === "School Sandbox") {
        globalThis.location.href = SANDBOX_ADMIN_HOME;
      } else {
        globalThis.location.href = role.route;
      }
    } catch (e) {
      setError(e.message || "Login failed. Is the backend running?");
      setBusy("");
    }
  }

  // Only show sandbox login form in sandbox mode
  if (IS_SANDBOX) {
    return (
      <div className="lp-root">
        <div className="lp-brand">
          <div className="lp-brand-top">
            <div className="lp-mark">
              <CrownSVG size={50} />
              <div>
                <div className="lp-mark-name">Crown</div>
                <div className="lp-mark-tag">School Management Platform</div>
              </div>
            </div>
            <div className="lp-gold-rule" />
            <h1 className="lp-headline">Sandbox Login</h1>
            <p className="lp-body-copy">Sign in to your sandbox environment using the prefilled credentials below. Only sandbox logins are permitted in this environment.</p>
          </div>
          <div className="lp-brand-bottom">
            <div className="lp-school-label">Institution</div>
            <div className="lp-school-name">Heritage Christian Academy</div>
          </div>
        </div>
        <div className="lp-panel">
          <div className="lp-form">
            <h1 className="lp-welcome">Sandbox Login</h1>
            <p className="lp-prompt">Use the prefilled credentials below to access your sandbox.</p>
            {error && <div className="lp-err">{error}</div>}
            <form onSubmit={e => { e.preventDefault(); login(ROLES[0]); }}>
              <label htmlFor="sandbox-school" style={{ fontWeight: 600, fontSize: 13 }}>School</label>
              <select
                id="sandbox-school"
                value={selectedSchoolId}
                onChange={(e) => setSelectedSchoolId(e.target.value)}
                className="lp-input"
                style={{ marginBottom: 12 }}
              >
                {schools.map((school) => (
                  <option key={school.id} value={school.id}>{school.name}</option>
                ))}
              </select>
              <label htmlFor="sandbox-email" style={{ fontWeight: 600, fontSize: 13 }}>Email</label>
              <input id="sandbox-email" type="email" value={sandboxEmail} readOnly className="lp-input" style={{ marginBottom: 12 }} />
              <label htmlFor="sandbox-pass" style={{ fontWeight: 600, fontSize: 13 }}>Password</label>
              <input id="sandbox-pass" type="password" value={sandboxPass} readOnly className="lp-input" style={{ marginBottom: 10 }} />
              <div className="lp-notice" style={{ marginBottom: 12 }}>
                Sandbox only. No production records are available from this sign-in.
              </div>
              <div style={{ fontSize: 12, color: "#6C88A2", marginBottom: 18 }}>These credentials are valid only for your sandbox. Platform admin and demo/global accounts are not available here.</div>
              <button type="submit" disabled={busy} style={{ width: "100%", padding: 12, borderRadius: 7, background: "#0F2C4C", color: "#fff", fontWeight: 700, fontSize: 15, border: "none", cursor: busy ? "wait" : "pointer" }}>{busy ? "Signing in..." : "Sign in to Sandbox"}</button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ...existing code for non-sandbox environments...
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .lp-root {
          display: flex;
          min-height: 100vh;
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        /*  Brand column  */
        .lp-brand {
          width: 400px;
          flex-shrink: 0;
          background: linear-gradient(160deg, #071A2E 0%, #0F2C4C 45%, #0D3660 100%);
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          padding: 52px 44px;
          position: relative;
          overflow: hidden;
        }

        .lp-brand::before {
          content: '';
          position: absolute;
          top: -140px; right: -140px;
          width: 420px; height: 420px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(28,78,128,0.5) 0%, transparent 68%);
          pointer-events: none;
        }

        .lp-brand::after {
          content: '';
          position: absolute;
          bottom: -120px; left: -100px;
          width: 360px; height: 360px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(198,165,74,0.07) 0%, transparent 70%);
          pointer-events: none;
        }

        .lp-brand-top { position: relative; z-index: 1; }

        .lp-mark {
          display: flex;
          align-items: center;
          gap: 14px;
          margin-bottom: 44px;
        }

        .lp-mark-name {
          color: #fff;
          font-size: 24px;
          font-weight: 700;
          letter-spacing: -0.3px;
          line-height: 1;
        }

        .lp-mark-tag {
          color: rgba(255,255,255,0.42);
          font-size: 10.5px;
          font-weight: 500;
          letter-spacing: 0.2px;
          margin-top: 4px;
        }

        .lp-gold-rule {
          width: 32px; height: 2px;
          background: #C6A54A;
          border-radius: 2px;
          margin-bottom: 22px;
        }

        .lp-headline {
          color: #fff;
          font-size: 28px;
          font-weight: 300;
          line-height: 1.38;
          letter-spacing: -0.2px;
          margin-bottom: 14px;
        }

        .lp-headline strong {
          font-weight: 700;
        }

        .lp-body-copy {
          color: rgba(255,255,255,0.46);
          font-size: 13px;
          font-weight: 400;
          line-height: 1.65;
        }

        .lp-brand-bottom {
          position: relative;
          z-index: 1;
          padding-top: 20px;
          border-top: 1px solid rgba(255,255,255,0.09);
        }

        .lp-school-label {
          color: rgba(255,255,255,0.32);
          font-size: 10px;
          font-weight: 500;
          letter-spacing: 1.4px;
          text-transform: uppercase;
          margin-bottom: 4px;
        }

        .lp-school-name {
          color: rgba(255,255,255,0.6);
          font-size: 13px;
          font-weight: 600;
        }

        /*  Login column  */
        .lp-panel {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #F1F5FA;
          padding: 40px 32px;
          overflow-y: auto;
        }

        .lp-form {
          width: 100%;
          max-width: 456px;
        }

        .lp-input {
          width: 100%;
          padding: 9px 10px;
          border: 1px solid #D5E0EC;
          border-radius: 6px;
          font-size: 13px;
          color: #0D1F35;
          background: #fff;
        }

        .lp-input:focus {
          outline: 2px solid rgba(26, 111, 168, 0.25);
          border-color: #1A6FA8;
        }

        .lp-welcome {
          font-size: 22px;
          font-weight: 700;
          color: #0D1F35;
          letter-spacing: -0.3px;
          margin-bottom: 3px;
        }

        .lp-prompt {
          font-size: 13.5px;
          color: #2f4358;
          font-weight: 400;
          margin-bottom: 22px;
        }

        .lp-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 7px;
          margin-bottom: 18px;
        }

        .lp-err {
          margin-bottom: 14px;
          padding: 10px 13px;
          background: #FEF2F2;
          border: 1px solid #FECACA;
          border-left: 3px solid #DC2626;
          border-radius: 6px;
          color: #991B1B;
          font-size: 12.5px;
          font-weight: 500;
          line-height: 1.5;
        }

        .lp-notice {
          padding: 9px 11px;
          border-radius: 6px;
          border: 1px solid #FCD34D;
          background: #FFFBEB;
          color: #92400E;
          font-size: 12px;
          line-height: 1.4;
          font-weight: 600;
        }

        .lp-credentials {
          margin-bottom: 12px;
          padding: 11px 12px;
          background: #F7FAFE;
          border: 1px solid #DCE7F2;
          border-radius: 7px;
        }

        .lp-credentials strong {
          display: block;
          color: #113457;
          font-size: 12px;
          margin-bottom: 6px;
        }

        .lp-credentials-row {
          font-size: 12px;
          color: #274766;
          line-height: 1.5;
        }

        .lp-sep {
          display: flex;
          align-items: center;
          gap: 11px;
          margin-bottom: 13px;
        }

        .lp-sep-line { flex: 1; height: 1px; background: #D5E0EC; }

        .lp-sep-text {
          font-size: 11px;
          color: #3d5268;
          font-weight: 500;
          white-space: nowrap;
        }

        .lp-ms {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 9px;
          width: 100%;
          padding: 11px 16px;
          background: #fff;
          border: 1px solid #D2DFEE;
          border-radius: 7px;
          cursor: pointer;
          font-family: inherit;
          font-size: 13px;
          font-weight: 600;
          color: #1A3050;
          box-shadow: 0 1px 3px rgba(15,44,76,0.05);
          outline: none;
          transition: all 0.14s ease;
          margin-bottom: 22px;
        }

        .lp-ms:hover {
          border-color: #0F2C4C;
          background: #F5F8FF;
          box-shadow: 0 2px 12px rgba(15,44,76,0.1);
        }

        .lp-foot {
          font-size: 11px;
          color: #3d5268;
          text-align: center;
          line-height: 1.55;
        }

        @keyframes lp-spin { to { transform: rotate(360deg); } }

        @media (max-width: 800px) {
          .lp-root { flex-direction: column; }
          .lp-brand { width: 100%; padding: 28px 24px 24px; }
          .lp-headline { font-size: 22px; }
          .lp-body-copy { display: none; }
          .lp-brand-bottom { display: none; }
          .lp-panel { padding: 24px 14px 28px; align-items: flex-start; }
          .lp-form { max-width: 100%; }
          .lp-grid { grid-template-columns: 1fr; }
        }

        @media (max-width: 480px) {
          .lp-mark-name { font-size: 21px; }
          .lp-welcome { font-size: 19px; }
          .lp-prompt { font-size: 12.5px; margin-bottom: 16px; }
          .lp-ms { margin-bottom: 16px; }
        }
      `}</style>

      <div className="lp-root">

        {/* Brand panel */}
        <div className="lp-brand">
          <div className="lp-brand-top">
            <div className="lp-mark">
              <CrownSVG size={50} />
              <div>
                <div className="lp-mark-name">Crown</div>
                <div className="lp-mark-tag">School Management Platform</div>
              </div>
            </div>

            <div className="lp-gold-rule" />

            <h1 className="lp-headline">
              One platform.<br />
              <strong>Every stakeholder.</strong>
            </h1>
            <p className="lp-body-copy">
              Purpose-built for independent schools  financial aid,
              admissions, governance, and academics in a single
              integrated system.
            </p>
          </div>

          <div className="lp-brand-bottom">
            <div className="lp-school-label">Institution</div>
            <div className="lp-school-name">Heritage Christian Academy</div>
          </div>
        </div>

        {/* Login panel */}
        <div className="lp-panel">
          <div className="lp-form">

            <h1 className="lp-welcome">Login</h1>
            <h2 className="lp-welcome">Welcome back</h2>
            <p className="lp-prompt">Select your role to access the correct dashboard and permissions scope.</p>

            <label htmlFor="login-school" style={{ fontWeight: 600, fontSize: 13, display: "block", marginBottom: 6 }}>School</label>
            <select
              id="login-school"
              value={selectedSchoolId}
              onChange={(e) => setSelectedSchoolId(e.target.value)}
              className="lp-input"
              style={{ marginBottom: 12 }}
            >
              {schools.map((school) => (
                <option key={school.id} value={school.id}>{school.name}</option>
              ))}
            </select>

            <div className="lp-notice" style={{ marginBottom: 12 }}>
              Training/demo environment only. No real student or family data is exposed.
            </div>

            <div className="lp-credentials">
              <strong>Prefilled Operator Credentials</strong>
              <div className="lp-credentials-row">Email: {DEMO_USER}</div>
              <div className="lp-credentials-row">Password: {DEMO_PASS}</div>
            </div>

            {error && <div className="lp-err">{error}</div>}

            <div className="lp-grid">
              {ROLES.map((role) => (
                <RoleCard key={role.label} role={role} busy={busy} onLogin={login} />
              ))}
            </div>

            <div className="lp-sep">
              <div className="lp-sep-line" />
              <span className="lp-sep-text">or sign in with your school account</span>
              <div className="lp-sep-line" />
            </div>

            <button
              className="lp-ms"
              onClick={() => { globalThis.location.href = API_BASE + "/auth/microsoft/login/"; }}
            >
              <MsIcon />
              Continue with Microsoft 365
            </button>

            <p className="lp-foot">
              Access is restricted to provisioned accounts.
              Contact your administrator or {SUPPORT_EMAIL} for support.
            </p>

          </div>
        </div>

      </div>
    </>
  );
}
