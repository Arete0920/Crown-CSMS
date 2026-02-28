/**
 * PromotionWizard.jsx
 * Wizard #24 — Student Promotion / Rollover Map
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/promotion-wizard/sessions/";
const GRADES = ["PK3","PK4","K","1","2","3","4","5","6","7","8","9","10","11","12","GRAD"];

async function _post(path, body) {
  const r = await apiFetch(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(json.error || `HTTP ${r.status}`);
  return json;
}

function emptyRule(ordering) { return { from_grade_code: "K", to_grade_code: "1", ordering }; }

export default function PromotionWizard() {
  const [phase, setPhase] = useState("configure");
  const [rules, setRules] = useState([emptyRule(0)]);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  function updateRow(i, k, v) {
    setRules(prev => prev.map((row, idx) => idx === i ? { ...row, [k]: v } : row));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErr(null);
    try {
      const sess = await _post(BASE);
      const sid = sess.session_id;
      await _post(`${BASE}${sid}/configure/`, { rules });
      const r = await _post(`${BASE}${sid}/commit/`);
      setResult(r);
      setPhase("done");
    } catch (ex) { setErr(ex.message); }
  }

  return (
    <CrownLayout title="Promotion Map Setup">
      {phase === "configure" && (
        <form onSubmit={handleSubmit}>
          <h2>Step 1 — Promotion Rules</h2>
          {rules.map((row, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <label>From: <select value={row.from_grade_code} onChange={e => updateRow(i, "from_grade_code", e.target.value)}>{GRADES.map(g => <option key={g}>{g}</option>)}</select></label>
              <label>To: <select value={row.to_grade_code} onChange={e => updateRow(i, "to_grade_code", e.target.value)}>{GRADES.map(g => <option key={g}>{g}</option>)}</select></label>
            </div>
          ))}
          <button type="button" onClick={() => setRules(p => [...p, emptyRule(p.length)])}>+ Add Rule</button>
          {err && <p style={{ color: "red" }}>{err}</p>}
          <button type="submit">Commit Promotion Map</button>
        </form>
      )}
      {phase === "done" && <div><h2>Done</h2><p>Created: {result?.created} · Updated: {result?.updated} · Total: {result?.total}</p></div>}
    </CrownLayout>
  );
}
