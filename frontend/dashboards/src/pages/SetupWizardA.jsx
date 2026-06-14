import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/guardian-household-wizard/sessions/";

async function send(path, method, body) {
  const response = await apiFetch(path, { method, body: body ? JSON.stringify(body) : undefined });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

export default function SetupWizardA() {
  const [step, setStep] = useState("household");
  const [sessionId, setSessionId] = useState("");
  const [householdJson, setHouseholdJson] = useState('{"name":"Sample Household","address":{}}');
  const [guardianJson, setGuardianJson] = useState('[{"name":"Sample Guardian","email":"guardian@example.com","custody_type":"primary"}]');
  const [studentJson, setStudentJson] = useState('[{"student_id":"","relationship":"parent"}]');
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function run(work) {
    setError("");
    try { await work(); } catch (err) { setError(err.message || "Request failed"); }
  }

  return (
    <CrownLayout title="Guardian & Household Setup">
      {error && <p style={{ color: "var(--crown-danger)" }}>{error}</p>}
      {step === "household" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { const session = await send(BASE, "POST"); setSessionId(session.session_id); await send(`${BASE}${session.session_id}/configure/`, "POST", { household_data: JSON.parse(householdJson) }); setStep("guardians"); }); }}><h2>Household</h2><textarea rows={8} value={householdJson} onChange={(event) => setHouseholdJson(event.target.value)} style={{ width: "100%" }} /><button type="submit">Save household</button></form>}
      {step === "guardians" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { await send(`${BASE}${sessionId}/add_guardians/`, "POST", { guardian_data: JSON.parse(guardianJson) }); setStep("students"); }); }}><h2>Guardians</h2><textarea rows={8} value={guardianJson} onChange={(event) => setGuardianJson(event.target.value)} style={{ width: "100%" }} /><button type="submit">Save guardians</button></form>}
      {step === "students" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { await send(`${BASE}${sessionId}/link_students/`, "POST", { link_data: JSON.parse(studentJson) }); setStep("commit"); }); }}><h2>Student links</h2><textarea rows={8} value={studentJson} onChange={(event) => setStudentJson(event.target.value)} style={{ width: "100%" }} /><button type="submit">Save links</button></form>}
      {step === "commit" && <button type="button" onClick={() => run(async () => { await send(`${BASE}${sessionId}/commit/`, "POST", { confirm: true }); const verified = await send(`${BASE}${sessionId}/verify/`, "GET"); setResult(verified); setStep("done"); })}>Commit and verify</button>}
      {step === "done" && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </CrownLayout>
  );
}
