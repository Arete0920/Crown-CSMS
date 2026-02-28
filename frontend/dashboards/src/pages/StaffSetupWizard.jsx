/**
 * StaffSetupWizard.jsx
 * Wizard #21 — Staff & Roles Setup
 * Steps: configure (roster) → done
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/staff-setup-wizard/sessions/";

async function _post(path, body) {
  const r = await apiFetch(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(json.error || `HTTP ${r.status}`);
  return json;
}

function emptyStaff() { return { email: "", first_name: "", last_name: "", is_teacher: true, is_admin: false }; }

export default function StaffSetupWizard() {
  const [phase, setPhase] = useState("configure");
  const [sessionId, setSessionId] = useState(null);
  const [roster, setRoster] = useState([emptyStaff()]);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  async function handleConfigure(e) {
    e.preventDefault();
    setErr(null);
    try {
      const sess = await _post(BASE);
      const sid = sess.session_id;
      setSessionId(sid);
      await _post(`${BASE}${sid}/configure/`, { roster });
      const r = await _post(`${BASE}${sid}/commit/`);
      setResult(r);
      setPhase("done");
    } catch (ex) { setErr(ex.message); }
  }

  function updateRow(i, k, v) {
    setRoster(prev => prev.map((row, idx) => idx === i ? { ...row, [k]: v } : row));
  }

  return (
    <CrownLayout title="Staff & Roles Setup">
      {phase === "configure" && (
        <form onSubmit={handleConfigure}>
          <h2>Step 1 — Staff Roster</h2>
          {roster.map((row, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <input placeholder="Email" value={row.email} onChange={e => updateRow(i, "email", e.target.value)} required />
              <input placeholder="First name" value={row.first_name} onChange={e => updateRow(i, "first_name", e.target.value)} />
              <input placeholder="Last name" value={row.last_name} onChange={e => updateRow(i, "last_name", e.target.value)} />
              <label><input type="checkbox" checked={row.is_teacher} onChange={e => updateRow(i, "is_teacher", e.target.checked)} /> Teacher</label>
              <label><input type="checkbox" checked={row.is_admin} onChange={e => updateRow(i, "is_admin", e.target.checked)} /> Admin</label>
            </div>
          ))}
          <button type="button" onClick={() => setRoster(p => [...p, emptyStaff()])}>+ Add Row</button>
          {err && <p style={{ color: "red" }}>{err}</p>}
          <button type="submit">Commit Staff</button>
        </form>
      )}
      {phase === "done" && (
        <div>
          <h2>Done</h2>
          <p>Created: {result?.created} · Updated: {result?.updated} · Total: {result?.total}</p>
        </div>
      )}
    </CrownLayout>
  );
}
