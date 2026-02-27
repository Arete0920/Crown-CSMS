/**
 * AcademicYearWizard.jsx
 *
 * Wizard #15 — Academic Year Rollover
 * Guides admin staff through creating a new academic year with term definitions.
 *
 * Steps:
 *   1. Configure — year name, start date, end date
 *   2. Terms     — define academic terms (code, name, dates, ordering)
 *   3. Done      — commit and verify (new year set as current, previous deactivated)
 *
 * MVP: no enrollment/section migration. Year + terms only.
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/academic-year-wizard/sessions/";

function emptyTerm(idx) {
  return {
    code:        "",
    name:        "",
    school_year: "",
    start_date:  "",
    end_date:    "",
    ordering:    idx,
  };
}

function Step({ title, children }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ marginBottom: 12 }}>{title}</h3>
      {children}
    </div>
  );
}

export default function AcademicYearWizard() {
  const [phase, setPhase]         = useState("configure"); // configure | terms | done | error
  const [sessionId, setSessionId] = useState(null);
  const [result, setResult]       = useState(null);
  const [err, setErr]             = useState(null);
  const [busy, setBusy]           = useState(false);

  const [config, setConfig] = useState({
    year_name:  "",
    start_date: "",
    end_date:   "",
  });

  const [terms, setTerms] = useState([emptyTerm(0)]);

  function configField(name) {
    return {
      value:    config[name],
      onChange: (e) => setConfig((c) => ({ ...c, [name]: e.target.value })),
    };
  }

  function termField(idx, name) {
    return {
      value:    terms[idx][name],
      onChange: (e) => {
        const val = name === "ordering" ? parseInt(e.target.value, 10) || 0 : e.target.value;
        setTerms((ts) => ts.map((t, i) => i === idx ? { ...t, [name]: val } : t));
      },
    };
  }

  function addTerm() {
    setTerms((ts) => [...ts, emptyTerm(ts.length)]);
  }

  function removeTerm(idx) {
    setTerms((ts) => ts.filter((_, i) => i !== idx));
  }

  async function handleConfigure(e) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      // 1. Create session
      const created = await apiFetch(BASE, { method: "POST" });
      const sid = created.session_id;
      setSessionId(sid);

      // 2. Configure
      await apiFetch(`${BASE}${sid}/configure/`, {
        method: "POST",
        body: JSON.stringify(config),
      });

      setPhase("terms");
    } catch (ex) {
      setErr(ex.message || "Configure step failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleTerms(e) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      // 3. Set terms
      await apiFetch(`${BASE}${sessionId}/terms/`, {
        method: "POST",
        body: JSON.stringify({ terms }),
      });

      // 4. Commit
      const committed = await apiFetch(`${BASE}${sessionId}/commit/`, { method: "POST" });

      // 5. Verify
      const verified = await apiFetch(`${BASE}${sessionId}/verify/`);

      setResult({ ...committed.result, ...verified });
      setPhase("done");
    } catch (ex) {
      setErr(ex.message || "Terms/commit step failed.");
    } finally {
      setBusy(false);
    }
  }

  function handleRestart() {
    setPhase("configure");
    setErr(null);
    setResult(null);
    setSessionId(null);
    setConfig({ year_name: "", start_date: "", end_date: "" });
    setTerms([emptyTerm(0)]);
  }

  if (phase === "done") {
    return (
      <CrownLayout title="Academic Year Rollover" subtitle="Wizard #15 — Academic Year Rollover">
        <Step title="Academic Year Created">
          <p style={{ color: "green" }}>
            {result?.message || "Academic year created successfully."}
          </p>
          <ul>
            <li><strong>Year ID:</strong> {result?.academic_year_id}</li>
            <li><strong>Year Name:</strong> {result?.year_name}</li>
            <li><strong>Is Current:</strong> {result?.is_current ? "Yes" : "No"}</li>
            <li><strong>Terms created:</strong> {result?.terms_created}</li>
            <li><strong>Terms updated:</strong> {result?.terms_updated}</li>
            <li><strong>Total terms:</strong> {result?.term_count}</li>
            {result?.deactivated_count > 0 && (
              <li><strong>Previous years deactivated:</strong> {result.deactivated_count}</li>
            )}
          </ul>
          <button onClick={handleRestart}>Create Another</button>
        </Step>
      </CrownLayout>
    );
  }

  if (phase === "terms") {
    return (
      <CrownLayout title="Academic Year Rollover" subtitle="Wizard #15 — Academic Year Rollover">
        <Step title="Step 2 of 2 — Academic Terms">
          {err && <p style={{ color: "red" }}>{err}</p>}
          <form onSubmit={handleTerms}>
            {terms.map((term, idx) => (
              <div key={idx} style={{ border: "1px solid #ddd", borderRadius: 4, padding: 12, marginBottom: 12 }}>
                <div style={{ marginBottom: 6 }}>
                  <label>Code&nbsp;
                    <input
                      {...termField(idx, "code")}
                      required
                      pattern="[A-Za-z0-9_\-]{1,24}"
                      title="1-24 alphanumeric, dash, or underscore"
                      placeholder="e.g. FALL-2027"
                      style={{ width: 160 }}
                    />
                  </label>
                  &nbsp;
                  <label>Name&nbsp;
                    <input {...termField(idx, "name")} required placeholder="e.g. Fall 2027" style={{ width: 200 }} />
                  </label>
                  &nbsp;
                  <label>School Year&nbsp;
                    <input {...termField(idx, "school_year")} placeholder="e.g. 2027-28" style={{ width: 100 }} />
                  </label>
                </div>
                <div style={{ marginBottom: 6 }}>
                  <label>Start Date&nbsp;
                    <input type="date" {...termField(idx, "start_date")} />
                  </label>
                  &nbsp;
                  <label>End Date&nbsp;
                    <input type="date" {...termField(idx, "end_date")} />
                  </label>
                  &nbsp;
                  <label>Order&nbsp;
                    <input type="number" min="0" {...termField(idx, "ordering")} style={{ width: 60 }} />
                  </label>
                  &nbsp;
                  {terms.length > 1 && (
                    <button type="button" onClick={() => removeTerm(idx)} style={{ color: "red" }}>
                      Remove
                    </button>
                  )}
                </div>
              </div>
            ))}
            <div style={{ marginBottom: 12 }}>
              <button type="button" onClick={addTerm}>+ Add Term</button>
            </div>
            <button type="submit" disabled={busy}>{busy ? "Saving…" : "Commit Rollover"}</button>
          </form>
        </Step>
      </CrownLayout>
    );
  }

  // phase === "configure"
  return (
    <CrownLayout title="Academic Year Rollover" subtitle="Wizard #15 — Academic Year Rollover">
      <Step title="Step 1 of 2 — Year Details">
        {err && <p style={{ color: "red" }}>{err}</p>}
        <p style={{ color: "#666", marginBottom: 16 }}>
          This wizard creates a new academic year and marks it as current.
          The previous current year will be deactivated automatically.
        </p>
        <form onSubmit={handleConfigure}>
          <div style={{ marginBottom: 10 }}>
            <label>Year Name&nbsp;
              <input {...configField("year_name")} required placeholder="e.g. 2027-2028" style={{ width: 200 }} />
            </label>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label>Start Date&nbsp;
              <input type="date" {...configField("start_date")} required />
            </label>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label>End Date&nbsp;
              <input type="date" {...configField("end_date")} required />
            </label>
          </div>
          <button type="submit" disabled={busy}>{busy ? "Saving…" : "Next: Define Terms →"}</button>
        </form>
      </Step>
    </CrownLayout>
  );
}
