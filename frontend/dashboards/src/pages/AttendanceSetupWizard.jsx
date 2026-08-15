import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/attendance-codes-wizard/sessions/";

async function send(path, method, body) {
  const response = await apiFetch(path, { method, body: body ? JSON.stringify(body) : undefined });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || data.detail || `HTTP ${response.status}`);
  return data;
}

export default function AttendanceSetupWizard() {
  const [step, setStep] = useState("setup");
  const [sessionId, setSessionId] = useState("");
  const [policyJson, setPolicyJson] = useState('{"school_year":"2026-2027","label":"Default Attendance Policy","default_absent_code":"A"}');
  const [rowsJson, setRowsJson] = useState('[{"code":"A","label":"Absent","excused":false,"counts_as_absent":true}]');
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function run(work) {
    setError("");
    try { await work(); } catch (err) { setError(err.message || "Request failed"); }
  }

  return (
    <CrownLayout title="Attendance Setup">
      {error && <p role="alert" style={{ color: "var(--crown-danger)" }}>{error}</p>}
      {step === "setup" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { const policy = JSON.parse(policyJson); const session = await send(BASE, "POST"); setSessionId(session.session_id); await send(`${BASE}${session.session_id}/configure/`, "POST", { policy_config: policy }); setStep("rows"); }); }}><h2>Attendance policy</h2><label htmlFor="attendance-policy-json">Policy configuration</label><textarea id="attendance-policy-json" rows={8} value={policyJson} onChange={(event) => setPolicyJson(event.target.value)} style={{ width: "100%" }} /><button type="submit">Continue</button></form>}
      {step === "rows" && <form onSubmit={(event) => { event.preventDefault(); run(async () => { await send(`${BASE}${sessionId}/stage_codes/`, "POST", { codes_staged: JSON.parse(rowsJson) }); setStep("commit"); }); }}><h2>Attendance codes</h2><label htmlFor="attendance-codes-json">Codes</label><textarea id="attendance-codes-json" rows={10} value={rowsJson} onChange={(event) => setRowsJson(event.target.value)} style={{ width: "100%" }} /><button type="submit">Continue</button></form>}
      {step === "commit" && <><h2>Review and commit</h2><button type="button" onClick={() => run(async () => { await send(`${BASE}${sessionId}/commit/`, "POST", { confirm: true }); const verified = await send(`${BASE}${sessionId}/verify/`, "GET"); setResult(verified); setStep("done"); })}>Commit and verify</button></>}
      {step === "done" && <><h2>Attendance configuration verified</h2><pre data-testid="attendance-verification-result">{JSON.stringify(result, null, 2)}</pre></>}
    </CrownLayout>
  );
}
