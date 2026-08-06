/**
 * CourseCatalogWizard.jsx
 * Wizard #22 — Course Catalog Setup
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/course-catalog-wizard/sessions/";

async function _post(path, body) {
  const r = await apiFetch(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(json.error || `HTTP ${r.status}`);
  return json;
}

function emptyCourse() { return { code: "", name: "", credits: 1.0 }; }

export default function CourseCatalogWizard() {
  const [phase, setPhase] = useState("configure");
  const [catalog, setCatalog] = useState([emptyCourse()]);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  function updateRow(i, k, v) {
    setCatalog(prev => prev.map((row, idx) => idx === i ? { ...row, [k]: v } : row));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErr(null);
    try {
      const sess = await _post(BASE);
      const sid = sess.session_id;
      await _post(`${BASE}${sid}/configure/`, { catalog });
      const r = await _post(`${BASE}${sid}/commit/`);
      setResult(r);
      setPhase("done");
    } catch (ex) { setErr(ex.message); }
  }

  return (
    <CrownLayout title="Course Catalog Setup">
      {phase === "configure" && (
        <form onSubmit={handleSubmit}>
          <h2>Step 1 — Course Catalog</h2>
          {catalog.map((row, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <input placeholder="Code (e.g. ENG1)" value={row.code} onChange={e => updateRow(i, "code", e.target.value)} required />
              <input placeholder="Name" value={row.name} onChange={e => updateRow(i, "name", e.target.value)} required />
              <input type="number" step="0.5" placeholder="Credits" value={row.credits} onChange={e => updateRow(i, "credits", parseFloat(e.target.value))} />
            </div>
          ))}
          <button type="button" onClick={() => setCatalog(p => [...p, emptyCourse()])}>+ Add Course</button>
          {err && <p style={{ color: "var(--crown-danger)" }}>{err}</p>}
          <button type="submit">Commit Catalog</button>
        </form>
      )}
      {phase === "done" && <div><h2>Done</h2><p>Created: {result?.created} · Updated: {result?.updated} · Total: {result?.total}</p></div>}
    </CrownLayout>
  );
}
