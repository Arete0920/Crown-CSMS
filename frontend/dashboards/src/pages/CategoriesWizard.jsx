import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch, apiJson } from "../lib/api.js";

const BASE = "/api/v1/grade-weights-wizard/sessions/";

async function send(path, method, body) {
  const response = await apiFetch(path, { method, body: body ? JSON.stringify(body) : undefined });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

export default function CategoriesWizard() {
  const [step, setStep] = useState("setup");
  const [sessionId, setSessionId] = useState("");
  const [sectionId, setSectionId] = useState("");
  const [sections, setSections] = useState([]);
  const [period, setPeriod] = useState("");
  const [rowsJson, setRowsJson] = useState('[{"name":"Tests","weight_pct":60},{"name":"Homework","weight_pct":40}]');
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    apiJson("/api/v1/academics/sections/?limit=200")
      .then((payload) => {
        if (!active) return;
        const rows = Array.isArray(payload) ? payload : (payload?.results || []);
        setSections(rows);
        if (rows.length === 1) setSectionId(rows[0].section_id);
      })
      .catch((err) => { if (active) setError(err.message || "Unable to load sections"); });
    return () => { active = false; };
  }, []);

  async function run(work) {
    setError("");
    try { await work(); } catch (err) { setError(err.message || "Request failed"); }
  }

  return (
    <CrownLayout title="Category Setup">
      {error && <p style={{ color: "var(--crown-danger)" }}>{error}</p>}
      {step === "setup" && (
        <form onSubmit={(event) => { event.preventDefault(); run(async () => {
          const session = await send(BASE, "POST");
          setSessionId(session.session_id);
          await send(`${BASE}${session.session_id}/configure/`, "POST", { section_id: sectionId, marking_period: period });
          setStep("rows");
        }); }}>
          <h2>Setup</h2>
          <label>Section&nbsp;
            <select aria-label="Section" value={sectionId} onChange={(event) => setSectionId(event.target.value)} required>
              <option value="">Select a section</option>
              {sections.map((section) => (
                <option key={section.section_id} value={section.section_id}>
                  {section.course_code || section.course_name || "Course"} — {section.term_code || "Section"}
                </option>
              ))}
            </select>
          </label>
          <label>Marking period&nbsp;
            <input placeholder="Marking period" value={period} onChange={(event) => setPeriod(event.target.value)} required />
          </label>
          <button type="submit">Continue</button>
        </form>
      )}
      {step === "rows" && (
        <form onSubmit={(event) => { event.preventDefault(); run(async () => {
          await send(`${BASE}${sessionId}/stage_categories/`, "POST", { categories_staged: JSON.parse(rowsJson) });
          setStep("commit");
        }); }}>
          <h2>Rows</h2>
          <textarea rows={10} value={rowsJson} onChange={(event) => setRowsJson(event.target.value)} style={{ width: "100%" }} />
          <button type="submit">Continue</button>
        </form>
      )}
      {step === "commit" && (
        <button type="button" onClick={() => run(async () => {
          await send(`${BASE}${sessionId}/commit/`, "POST", { confirm: true });
          const verified = await send(`${BASE}${sessionId}/verify/`, "GET");
          setResult(verified);
          setStep("done");
        })}>Commit and verify</button>
      )}
      {step === "done" && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </CrownLayout>
  );
}
