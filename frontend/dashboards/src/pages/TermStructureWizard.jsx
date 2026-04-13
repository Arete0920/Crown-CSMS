/**
 * TermStructureWizard.jsx
 *
 * Wizard #18 — Term & Marking Period Setup
 *
 * Steps:
 *   1. Configure — academic year ID, structure type (SEMESTER/QUARTER/TRIMESTER/CUSTOM)
 *   2. Periods   — define ordered marking periods (code, name, start_date, end_date)
 *                  full adjacency coverage required: periods must span ay.start_date ? ay.end_date
 *   3. Done      — commit result: term_structure_id, structure_type, periods created/updated
 */
import { useState, useCallback } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/term-structure-wizard/sessions/";

const STRUCTURE_TYPES = ["SEMESTER", "QUARTER", "TRIMESTER", "CUSTOM"];

function emptyPeriod() {
  return { code: "", name: "", start_date: "", end_date: "", is_grade_term: true };
}

async function _post(path, body) {
  const r = await apiFetch(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) {
    const msgs = json.errors || [json.error] || [`HTTP ${r.status}`];
    throw new Error(Array.isArray(msgs) ? msgs.join(" · ") : String(msgs));
  }
  return json;
}

export default function TermStructureWizard() {
  // Phases: configure | periods | done
  const [phase, setPhase] = useState("configure");
  const [sessionId, setSessionId] = useState(null);

  // Configure fields
  const [academicYearId,  setAcademicYearId]  = useState("");
  const [structureType,   setStructureType]   = useState("SEMESTER");

  // Periods
  const [periods, setPeriods] = useState([emptyPeriod(), emptyPeriod()]);

  // Result
  const [result, setResult] = useState(null);
  const [error, setError]   = useState(null);
  const [loading, setLoading] = useState(false);

  // -- Step helpers ----------------------------------------------------------

  const handleConfigure = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      // 1. Create session
      const sess = await _post(BASE, undefined);
      const sid  = sess.session_id;
      setSessionId(sid);

      // 2. Configure
      await _post(`${BASE}${sid}/configure/`, {
        academic_year_id: academicYearId.trim(),
        structure_type:   structureType,
      });

      setPhase("periods");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [academicYearId, structureType]);

  const handleSetPeriods = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const payload = periods
        .filter((p) => p.code.trim())
        .map((p) => ({
          code:          p.code.trim(),
          name:          p.name.trim(),
          start_date:    p.start_date.trim(),
          end_date:      p.end_date.trim(),
          is_grade_term: p.is_grade_term,
        }));

      await _post(`${BASE}${sessionId}/periods/`, payload);

      // Commit
      const res = await _post(`${BASE}${sessionId}/commit/`, undefined);

      setResult(res);
      setPhase("done");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId, periods]);

  // -- Period table helpers --------------------------------------------------

  const updatePeriod = (idx, field, value) => {
    setPeriods((prev) => prev.map((p, i) => (i === idx ? { ...p, [field]: value } : p)));
  };

  const addPeriod = () => setPeriods((prev) => [...prev, emptyPeriod()]);

  const removePeriod = (idx) =>
    setPeriods((prev) => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev);

  // -- Render ----------------------------------------------------------------

  return (
    <CrownLayout title="Term & Marking Period Setup">
      {phase === "configure" && (
        <div style={{ maxWidth: 520 }}>
          <h2>Step 1 — Configure Structure</h2>

          <div>Academic Year ID</div>
          <input
            type="text"
            value={academicYearId}
            onChange={(e) => setAcademicYearId(e.target.value)}
            placeholder="UUID of the academic year"
            style={{ display: "block", width: "100%", marginBottom: 12 }}
          />

          <div>Structure Type</div>
          <select
            value={structureType}
            onChange={(e) => setStructureType(e.target.value)}
            style={{ display: "block", width: "100%", marginBottom: 20 }}
          >
            {STRUCTURE_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>

          {error && <p style={{ color: "red" }}>{error}</p>}

          <button
            onClick={handleConfigure}
            disabled={loading || !academicYearId.trim()}
          >
            {loading ? "Saving…" : "Next: Set Periods ?"}
          </button>
        </div>
      )}

      {phase === "periods" && (
        <div style={{ maxWidth: 820 }}>
          <h2>Step 2 — Marking Periods</h2>
          <p style={{ color: "var(--crown-muted)", fontSize: 13 }}>
            Periods must be non-overlapping and cover the full academic year with no gaps.
            Adjacent periods: <code>period[i].end_date + 1 day == period[i+1].start_date</code>
          </p>

          <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 16 }}>
            <thead>
              <tr>
                {["Code", "Name", "Start Date", "End Date", "Grade Term?", ""].map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "4px 8px", borderBottom: "1px solid var(--crown-border)" }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {periods.map((p, idx) => (
                <tr key={idx}>
                  <td style={{ padding: "4px 8px" }}>
                    <input
                      type="text"
                      value={p.code}
                      onChange={(e) => updatePeriod(idx, "code", e.target.value)}
                      placeholder="S1"
                      style={{ width: 60 }}
                    />
                  </td>
                  <td style={{ padding: "4px 8px" }}>
                    <input
                      type="text"
                      value={p.name}
                      onChange={(e) => updatePeriod(idx, "name", e.target.value)}
                      placeholder="Semester 1"
                      style={{ width: 140 }}
                    />
                  </td>
                  <td style={{ padding: "4px 8px" }}>
                    <input
                      type="date"
                      value={p.start_date}
                      onChange={(e) => updatePeriod(idx, "start_date", e.target.value)}
                      style={{ width: 140 }}
                    />
                  </td>
                  <td style={{ padding: "4px 8px" }}>
                    <input
                      type="date"
                      value={p.end_date}
                      onChange={(e) => updatePeriod(idx, "end_date", e.target.value)}
                      style={{ width: 140 }}
                    />
                  </td>
                  <td style={{ padding: "4px 8px", textAlign: "center" }}>
                    <input
                      type="checkbox"
                      checked={p.is_grade_term}
                      onChange={(e) => updatePeriod(idx, "is_grade_term", e.target.checked)}
                    />
                  </td>
                  <td style={{ padding: "4px 8px" }}>
                    <button onClick={() => removePeriod(idx)} title="Remove">?</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <button onClick={addPeriod} style={{ marginBottom: 20 }}>+ Add Period</button>

          {error && <p style={{ color: "red" }}>{error}</p>}

          <div>
            <button onClick={() => { setPhase("configure"); setError(null); }} style={{ marginRight: 12 }}>
              ? Back
            </button>
            <button onClick={handleSetPeriods} disabled={loading}>
              {loading ? "Saving…" : "Commit Structure ?"}
            </button>
          </div>
        </div>
      )}

      {phase === "done" && result && (
        <div style={{ maxWidth: 600 }}>
          <h2>? Term Structure Committed</h2>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <tbody>
              {[
                ["Term Structure ID", result.term_structure_id],
                ["Structure Type",    result.structure_type],
                ["Academic Year",     result.academic_year_name],
                ["Active",            result.is_active ? "Yes" : "No"],
                ["Periods Created",   result.periods_created],
                ["Periods Updated",   result.periods_updated],
                ["Period Codes",      (result.period_codes || []).join(", ")],
              ].map(([label, value]) => (
                <tr key={label}>
                  <td style={{ padding: "6px 12px 6px 0", fontWeight: 600, width: 180 }}>{label}</td>
                  <td style={{ padding: "6px 0" }}>{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ marginTop: 16, color: "var(--crown-muted)" }}>{result.message}</p>
          <button
            onClick={() => {
              setPhase("configure");
              setSessionId(null);
              setResult(null);
              setError(null);
              setPeriods([emptyPeriod(), emptyPeriod()]);
              setAcademicYearId("");
              setStructureType("SEMESTER");
            }}
            style={{ marginTop: 16 }}
          >
            ? Set Up Another Term Structure
          </button>
        </div>
      )}
    </CrownLayout>
  );
}
