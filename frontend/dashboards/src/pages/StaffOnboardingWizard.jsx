/**
 * StaffOnboardingWizard.jsx
 *
 * Wizard #13 — Staff Onboarding
 * Guides the director through creating a new staff member (core.Staff record).
 *
 * Steps:
 *   1. Configure — first name, last name, email, role type
 *   2. Preview   — review what will be created, see duplicate warnings
 *   3. Commit    — create the Staff record
 *   4. Verify    — confirm the record exists
 *
 * MVP implementation: collect form fields, POST to backend wizard sessions.
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/staff-onboarding-wizard/sessions/";

const ROLES = [
  { value: "TEACHER",  label: "Teacher" },
  { value: "DIRECTOR", label: "Director" },
  { value: "ADMIN",    label: "Admin" },
  { value: "SUPPORT",  label: "Support" },
];

function Step({ title, children }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ marginBottom: 12 }}>{title}</h3>
      {children}
    </div>
  );
}

export default function StaffOnboardingWizard() {
  const [phase, setPhase]       = useState("form");   // form | preview | done | error
  const [sessionId, setSessionId] = useState(null);
  const [preview, setPreview]   = useState(null);
  const [result, setResult]     = useState(null);
  const [err, setErr]           = useState(null);
  const [busy, setBusy]         = useState(false);

  const [form, setForm] = useState({
    first_name: "",
    last_name:  "",
    email:      "",
    role_type:  "TEACHER",
  });

  function field(name) {
    return {
      value:    form[name],
      onChange: (e) => setForm((f) => ({ ...f, [name]: e.target.value })),
    };
  }

  async function handleConfigure(e) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      // 1. Create session
      const created = await apiFetch(BASE, { method: "POST" });
      const sid = created.session_id;
      setSessionId(sid);

      // 2. Configure
      await apiFetch(`${BASE}${sid}/configure/`, {
        method: "POST",
        body:   JSON.stringify(form),
      });

      // 3. Preview
      const prev = await apiFetch(`${BASE}${sid}/preview/`);
      setPreview(prev);
      setPhase("preview");
    } catch (ex) {
      setErr(ex.message || "Configuration failed");
    } finally {
      setBusy(false);
    }
  }

  async function handleCommit() {
    setBusy(true);
    setErr(null);
    try {
      const res = await apiFetch(`${BASE}${sessionId}/commit/`, { method: "POST" });
      // Verify
      await apiFetch(`${BASE}${sessionId}/verify/`);
      setResult(res.result);
      setPhase("done");
    } catch (ex) {
      setErr(ex.message || "Commit failed");
    } finally {
      setBusy(false);
    }
  }

  function handleReset() {
    setPhase("form");
    setSessionId(null);
    setPreview(null);
    setResult(null);
    setErr(null);
    setForm({ first_name: "", last_name: "", email: "", role_type: "TEACHER" });
  }

  return (
    <CrownLayout title="Staff Onboarding" subtitle="Create a new staff member">
      {err && (
        <p style={{ color: "var(--crown-danger)", marginBottom: 16 }}>
          {err}
        </p>
      )}

      {phase === "form" && (
        <Step title="Step 1: Staff Details">
          <form onSubmit={handleConfigure} style={{ display: "flex", flexDirection: "column", gap: 14, maxWidth: 420 }}>
            <label>
              First Name
              <input type="text" required style={{ display: "block", width: "100%", marginTop: 4 }} {...field("first_name")} />
            </label>
            <label>
              Last Name
              <input type="text" required style={{ display: "block", width: "100%", marginTop: 4 }} {...field("last_name")} />
            </label>
            <label>
              Email
              <input type="email" required style={{ display: "block", width: "100%", marginTop: 4 }} {...field("email")} />
            </label>
            <label>
              Role
              <select style={{ display: "block", width: "100%", marginTop: 4 }} {...field("role_type")}>
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </label>
            <button type="submit" disabled={busy}>
              {busy ? "Loading…" : "Preview →"}
            </button>
          </form>
        </Step>
      )}

      {phase === "preview" && preview && (
        <Step title="Step 2: Preview">
          {preview.warnings?.length > 0 && (
            <div style={{ background: "var(--crown-warn-bg)", padding: 10, borderRadius: 4, marginBottom: 12 }}>
              {preview.warnings.map((w, i) => <p key={i} style={{ margin: 0 }}>{w}</p>)}
            </div>
          )}
          <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 420 }}>
            <tbody>
              {Object.entries(preview.preview || {}).map(([k, v]) => (
                <tr key={k}>
                  <td style={{ padding: "6px 12px 6px 0", fontWeight: 600, whiteSpace: "nowrap" }}>{k}</td>
                  <td style={{ padding: "6px 0" }}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
            <button onClick={handleCommit} disabled={busy}>
              {busy ? "Creating…" : "Confirm & Create Staff"}
            </button>
            <button onClick={handleReset} style={{ background: "none", border: "1px solid currentColor" }}>
              ← Back
            </button>
          </div>
        </Step>
      )}

      {phase === "done" && result && (
        <Step title="Done">
          <p style={{ color: "var(--crown-ok)", fontWeight: 600 }}>
            {result.message || "Staff member created successfully."}
          </p>
          <dl style={{ maxWidth: 360 }}>
            <dt style={{ fontWeight: 600 }}>Staff ID</dt>
            <dd style={{ marginLeft: 0, marginBottom: 8 }}>{result.staff_id}</dd>
            <dt style={{ fontWeight: 600 }}>Email</dt>
            <dd style={{ marginLeft: 0, marginBottom: 8 }}>{result.email}</dd>
            <dt style={{ fontWeight: 600 }}>Role</dt>
            <dd style={{ marginLeft: 0, marginBottom: 8 }}>{result.role_type}</dd>
          </dl>
          <button onClick={handleReset}>Add Another Staff Member</button>
        </Step>
      )}
    </CrownLayout>
  );
}
