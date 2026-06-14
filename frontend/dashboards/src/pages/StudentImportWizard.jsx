import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/student-import-wizard/sessions/";

async function postJson(path, body) {
  const response = await apiFetch(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const json = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(json.error || `HTTP ${response.status}`);
  return json;
}

async function getJson(path) {
  const response = await apiFetch(path, { method: "GET" });
  const json = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(json.error || `HTTP ${response.status}`);
  return json;
}

const DEFAULT_COLUMN_MAP = {
  FirstName: "first_name",
  LastName: "last_name",
  Grade: "grade_level",
  ExternalId: "external_id",
};

const DEFAULT_ROWS = [
  {
    FirstName: "Sample",
    LastName: "Student",
    Grade: "9",
    ExternalId: "sample-001",
  },
];

export default function StudentImportWizard() {
  const [phase, setPhase] = useState("configure");
  const [sessionId, setSessionId] = useState(null);
  const [columnMap, setColumnMap] = useState(JSON.stringify(DEFAULT_COLUMN_MAP, null, 2));
  const [stagedRows, setStagedRows] = useState(JSON.stringify(DEFAULT_ROWS, null, 2));
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");

  async function handleConfigure(event) {
    event.preventDefault();
    setErr("");
    try {
      const session = await postJson(BASE);
      setSessionId(session.session_id);
      await postJson(`${BASE}${session.session_id}/configure/`, {
        column_map: JSON.parse(columnMap),
        staged_rows: JSON.parse(stagedRows),
      });
      setPhase("preview");
    } catch (error) {
      setErr(error.message);
    }
  }

  async function handlePreview() {
    setErr("");
    try {
      const data = await postJson(`${BASE}${sessionId}/preview/`, {});
      setPreview(data);
      setPhase("commit");
    } catch (error) {
      setErr(error.message);
    }
  }

  async function handleCommit() {
    setErr("");
    try {
      await postJson(`${BASE}${sessionId}/commit/`, { confirm: true });
      const verified = await getJson(`${BASE}${sessionId}/verify/`);
      setResult(verified);
      setPhase("done");
    } catch (error) {
      setErr(error.message);
    }
  }

  return (
    <CrownLayout title="Student Import" subtitle="Stage, preview, commit, and verify student import rows">
      {err && <p style={{ color: "var(--crown-danger)" }}>{err}</p>}

      {phase === "configure" && (
        <form onSubmit={handleConfigure}>
          <h2>Step 1 - Configure Import</h2>
          <label>
            Column map JSON
            <textarea
              value={columnMap}
              onChange={(event) => setColumnMap(event.target.value)}
              rows={8}
              style={{ display: "block", width: "100%", marginBottom: 12 }}
            />
          </label>
          <label>
            Staged rows JSON
            <textarea
              value={stagedRows}
              onChange={(event) => setStagedRows(event.target.value)}
              rows={8}
              style={{ display: "block", width: "100%", marginBottom: 12 }}
            />
          </label>
          <button type="submit">Configure Import</button>
        </form>
      )}

      {phase === "preview" && (
        <section>
          <h2>Step 2 - Preview</h2>
          <p>Session: {sessionId}</p>
          <button type="button" onClick={handlePreview}>Run Preview</button>
        </section>
      )}

      {phase === "commit" && (
        <section>
          <h2>Step 3 - Commit</h2>
          <pre>{JSON.stringify(preview, null, 2)}</pre>
          <button type="button" onClick={handleCommit}>Commit and Verify</button>
        </section>
      )}

      {phase === "done" && (
        <section>
          <h2>Done</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </section>
      )}
    </CrownLayout>
  );
}
