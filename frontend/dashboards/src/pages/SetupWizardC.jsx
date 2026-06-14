import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/" + "section" + "-staffing-wizard/sessions/";

async function send(path, method, body) {
  const response = await apiFetch(path, { method, body: body ? JSON.stringify(body) : undefined });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

export default function SetupWizardC() {
  const [step, setStep] = useState("setup");
  const [sessionId, setSessionId] = useState("");
  const [term, setTerm] = useState("");
  const [sectionsJson, setSectionsJson] = useState('[{"section_id":""}]');
  const [rowsJson, setRowsJson] = useState('[{"section_id":"","teacher_id":"","role":"primary"}]');
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function run(work) {
    setError("");
    try { await work(); } catch (err) { setError(err.message || "Request failed"); }
  }

  return (
    <CrownLayout title="Section Staffing">
      {error && <p style={{ color: "var(--crown-danger)" }}>{error}</p>}
      {step === "setup" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { const session = await send(BASE, "POST"); setSessionId(session.session_id); await send(`${BASE}${session.session_id}/configure/`, "POST", { term }); setStep("sections"); }); }}><h2>Setup</h2><input placeholder="Term" value={term} onChange={(event) => setTerm(event.target.value)} /><button type="submit">Continue</button></form>}
      {step === "sections" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { await send(`${BASE}${sessionId}/load_sections/`, "POST", { sections_pool: JSON.parse(sectionsJson) }); setStep("rows"); }); }}><h2>Sections</h2><textarea rows={8} value={sectionsJson} onChange={(event) => setSectionsJson(event.target.value)} style={{ width: "100%" }} /><button type="submit">Continue</button></form>}
      {step === "rows" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { await send(`${BASE}${sessionId}/stage_assignments/`, "POST", { assignments: JSON.parse(rowsJson) }); setStep("commit"); }); }}><h2>Rows</h2><textarea rows={8} value={rowsJson} onChange={(event) => setRowsJson(event.target.value)} style={{ width: "100%" }} /><button type="submit">Continue</button></form>}
      {step === "commit" && <button type="button" onClick={() => run(async () => { await send(`${BASE}${sessionId}/commit/`, "POST", { confirm: true }); const verified = await send(`${BASE}${sessionId}/verify/`, "GET"); setResult(verified); setStep("done"); })}>Commit and verify</button>}
      {step === "done" && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </CrownLayout>
  );
}
