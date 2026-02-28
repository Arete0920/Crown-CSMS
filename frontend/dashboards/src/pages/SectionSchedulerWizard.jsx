/**
 * SectionSchedulerWizard.jsx
 * Wizard #20 — Section Scheduler Seed
 * Steps: configure (ay_id, term_code) → sections → done
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/section-scheduler-wizard/sessions/";

async function _post(path, body) {
  const r = await apiFetch(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(json.error || `HTTP ${r.status}`);
  return json;
}

function emptySection() { return { section_code: "", course_code: "", template_code: "DEFAULT", block_code: "", teacher_email: "", room_code: "" }; }

export default function SectionSchedulerWizard() {
  const [phase, setPhase] = useState("configure");
  const [sessionId, setSessionId] = useState(null);
  const [ayId, setAyId] = useState("");
  const [termCode, setTermCode] = useState("");
  const [sections, setSections] = useState([emptySection()]);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  function updateSection(i, k, v) {
    setSections(prev => prev.map((row, idx) => idx === i ? { ...row, [k]: v } : row));
  }

  async function handleConfigure(e) {
    e.preventDefault();
    setErr(null);
    try {
      const sess = await _post(BASE);
      setSessionId(sess.session_id);
      await _post(`${BASE}${sess.session_id}/configure/`, { academic_year_id: ayId, term_code: termCode });
      setPhase("sections");
    } catch (ex) { setErr(ex.message); }
  }

  async function handleSections(e) {
    e.preventDefault();
    setErr(null);
    try {
      await _post(`${BASE}${sessionId}/sections/`, { sections });
      const r = await _post(`${BASE}${sessionId}/commit/`);
      setResult(r);
      setPhase("done");
    } catch (ex) { setErr(ex.message); }
  }

  return (
    <CrownLayout title="Section Scheduler Seed">
      {phase === "configure" && (
        <form onSubmit={handleConfigure}>
          <h2>Step 1 — Term Configuration</h2>
          <input placeholder="Academic Year ID (UUID)" value={ayId} onChange={e => setAyId(e.target.value)} required style={{ display: "block", marginBottom: 8 }} />
          <input placeholder="Term Code (e.g. S1, Q1)" value={termCode} onChange={e => setTermCode(e.target.value)} required style={{ display: "block", marginBottom: 8 }} />
          {err && <p style={{ color: "red" }}>{err}</p>}
          <button type="submit">Next: Define Sections</button>
        </form>
      )}
      {phase === "sections" && (
        <form onSubmit={handleSections}>
          <h2>Step 2 — Sections</h2>
          {sections.map((row, i) => (
            <div key={i} style={{ marginBottom: 8, display: "flex", gap: 4 }}>
              <input placeholder="Section Code" value={row.section_code} onChange={e => updateSection(i, "section_code", e.target.value)} required />
              <input placeholder="Course Code" value={row.course_code} onChange={e => updateSection(i, "course_code", e.target.value)} required />
              <input placeholder="Template (DEFAULT)" value={row.template_code} onChange={e => updateSection(i, "template_code", e.target.value)} required />
              <input placeholder="Block Code (P1)" value={row.block_code} onChange={e => updateSection(i, "block_code", e.target.value)} required />
              <input placeholder="Teacher Email" value={row.teacher_email} onChange={e => updateSection(i, "teacher_email", e.target.value)} />
              <input placeholder="Room Code" value={row.room_code} onChange={e => updateSection(i, "room_code", e.target.value)} />
            </div>
          ))}
          <button type="button" onClick={() => setSections(p => [...p, emptySection()])}>+ Add Section</button>
          {err && <p style={{ color: "red" }}>{err}</p>}
          <button type="submit">Commit Sections</button>
        </form>
      )}
      {phase === "done" && <div><h2>Done</h2><p>Created: {result?.created} · Updated: {result?.updated} · Total: {result?.total}</p></div>}
    </CrownLayout>
  );
}
