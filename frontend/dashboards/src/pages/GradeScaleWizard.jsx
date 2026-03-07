/**
 * GradeScaleWizard.jsx
 *
 * Wizard #17 — Grade Scale & Report Card Settings
 *
 * Steps:
 *   1. Configure — academic year, scale name, type (LETTER/PERCENT), rounding
 *   2. Bands     — define ordered, full-coverage percentage bands (A=90-100, etc.)
 *   3. Weights   — optional per-term weights (must sum to 10 000 bp = 100 %)
 *   4. Done      — commit result: scale_id, band count, weight count
 */
import { useState, useCallback } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/grade-scale-wizard/sessions/";

const SCALE_TYPES = ["LETTER", "PERCENT"];
const ROUNDING    = ["NEAREST", "FLOOR", "CEIL"];

function emptyBand() {
  return { label: "", min_pct: "", max_pct: "", gpa_points: "" };
}
function emptyWeight() {
  return { term_code: "", weight_bp: "" };
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

export default function GradeScaleWizard() {
  // Phases: configure | bands | weights | done
  const [phase, setPhase] = useState("configure");
  const [sessionId, setSessionId] = useState(null);

  // Configure fields
  const [academicYearId, setAcademicYearId] = useState("");
  const [scaleName, setScaleName]           = useState("");
  const [scaleType, setScaleType]           = useState("LETTER");
  const [rounding, setRounding]             = useState("NEAREST");

  // Bands
  const [bands, setBands] = useState([emptyBand()]);

  // Weights
  const [weightsEnabled, setWeightsEnabled] = useState(false);
  const [weights, setWeights]               = useState([emptyWeight()]);

  // Done
  const [result, setResult] = useState(null);

  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);

  // ─── PHASE 1: configure ───────────────────────────────────────────────────

  const handleConfigure = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const { session_id } = await _post(BASE);
      setSessionId(session_id);
      await _post(`${BASE}${session_id}/configure/`, {
        academic_year_id: academicYearId.trim(),
        name:       scaleName.trim(),
        scale_type: scaleType,
        rounding,
      });
      setPhase("bands");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [academicYearId, scaleName, scaleType, rounding]);

  // ─── PHASE 2: bands ───────────────────────────────────────────────────────

  const addBand    = () => setBands(prev => [...prev, emptyBand()]);
  const removeBand = idx => setBands(prev => prev.filter((_, i) => i !== idx));
  const updateBand = (idx, field, val) =>
    setBands(prev => prev.map((b, i) => (i === idx ? { ...b, [field]: val } : b)));

  const handleSetBands = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      await _post(`${BASE}${sessionId}/bands/`, {
        bands: bands.map(b => ({
          label:      b.label.trim(),
          min_pct:    parseInt(b.min_pct, 10),
          max_pct:    parseInt(b.max_pct, 10),
          ...(b.gpa_points !== "" ? { gpa_points: parseFloat(b.gpa_points) } : {}),
        })),
      });
      setPhase("weights");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId, bands]);

  // ─── PHASE 3: weights (optional) → commit ────────────────────────────────

  const addWeight    = () => setWeights(prev => [...prev, emptyWeight()]);
  const removeWeight = idx => setWeights(prev => prev.filter((_, i) => i !== idx));
  const updateWeight = (idx, field, val) =>
    setWeights(prev => prev.map((w, i) => (i === idx ? { ...w, [field]: val } : w)));

  const handleCommit = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      if (weightsEnabled) {
        await _post(`${BASE}${sessionId}/weights/`, {
          weights: weights.map(w => ({
            term_code: w.term_code.trim(),
            weight_bp: parseInt(w.weight_bp, 10),
          })),
        });
      }
      const commitData = await _post(`${BASE}${sessionId}/commit/`);
      await apiFetch(`${BASE}${sessionId}/verify/`);
      setResult(commitData.result);
      setPhase("done");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [sessionId, weightsEnabled, weights]);

  // ─── Reset ────────────────────────────────────────────────────────────────

  const reset = () => {
    setPhase("configure");
    setSessionId(null);
    setAcademicYearId("");
    setScaleName("");
    setScaleType("LETTER");
    setRounding("NEAREST");
    setBands([emptyBand()]);
    setWeightsEnabled(false);
    setWeights([emptyWeight()]);
    setResult(null);
    setError("");
  };

  // ─── RENDER ───────────────────────────────────────────────────────────────

  return (
    <CrownLayout
      title="Grade Scale Setup"
      subtitle="Wizard #17 — Define grading scale, bands, and optional term weights for an academic year."
    >
      {phase === "configure" && (
        <div style={{ maxWidth: 520 }}>
          <h2 style={h2}>Step 1: Configure Scale</h2>

          <label style={lbl}>
            Academic Year ID
            <input
              type="text"
              value={academicYearId}
              onChange={e => setAcademicYearId(e.target.value)}
              placeholder="Paste UUID from Wizard #15 / #16"
              style={inp}
            />
          </label>

          <label style={lbl}>
            Scale Name
            <input
              type="text"
              value={scaleName}
              onChange={e => setScaleName(e.target.value)}
              placeholder="e.g. 2027-2028 Letter Scale"
              style={inp}
            />
          </label>

          <label style={lbl}>
            Scale Type
            <select value={scaleType} onChange={e => setScaleType(e.target.value)} style={inp}>
              {SCALE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>

          <label style={lbl}>
            Rounding Policy
            <select value={rounding} onChange={e => setRounding(e.target.value)} style={inp}>
              {ROUNDING.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </label>

          {error && <p style={err}>{error}</p>}

          <button
            onClick={handleConfigure}
            disabled={loading || !academicYearId || !scaleName}
            style={btn}
          >
            {loading ? "Saving…" : "Next: Define Bands →"}
          </button>
        </div>
      )}

      {phase === "bands" && (
        <div style={{ maxWidth: 680 }}>
          <h2 style={h2}>Step 2: Grade Bands</h2>
          <p style={{ color: "var(--crown-muted)", marginBottom: 16 }}>
            Bands must together cover exactly 0–100 with no gaps or overlaps.
            Adjacent bands must satisfy <code>max[i] + 1 == min[i+1]</code>.
          </p>

          <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 12 }}>
            <thead>
              <tr style={{ background: "var(--crown-surface-2)" }}>
                <th style={th}>Label</th>
                <th style={th}>Min %</th>
                <th style={th}>Max %</th>
                <th style={th}>GPA pts (opt)</th>
                <th style={th}></th>
              </tr>
            </thead>
            <tbody>
              {bands.map((b, idx) => (
                <tr key={idx}>
                  <td style={td}>
                    <input
                      type="text"
                      value={b.label}
                      onChange={e => updateBand(idx, "label", e.target.value)}
                      placeholder="A"
                      style={{ ...inp, margin: 0 }}
                    />
                  </td>
                  <td style={td}>
                    <input
                      type="number"
                      min={0}
                      max={99}
                      value={b.min_pct}
                      onChange={e => updateBand(idx, "min_pct", e.target.value)}
                      style={{ ...inp, margin: 0, width: 70 }}
                    />
                  </td>
                  <td style={td}>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={b.max_pct}
                      onChange={e => updateBand(idx, "max_pct", e.target.value)}
                      style={{ ...inp, margin: 0, width: 70 }}
                    />
                  </td>
                  <td style={td}>
                    <input
                      type="number"
                      step="0.001"
                      value={b.gpa_points}
                      onChange={e => updateBand(idx, "gpa_points", e.target.value)}
                      placeholder="4.0"
                      style={{ ...inp, margin: 0, width: 70 }}
                    />
                  </td>
                  <td style={td}>
                    {bands.length > 1 && (
                      <button onClick={() => removeBand(idx)} style={rmBtn}>✕</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <button onClick={addBand} style={{ ...btn, background: "var(--crown-muted)", marginRight: 12 }}>
            + Add Band
          </button>

          {error && <p style={err}>{error}</p>}

          <button
            onClick={handleSetBands}
            disabled={loading || bands.some(b => !b.label || b.min_pct === "" || b.max_pct === "")}
            style={btn}
          >
            {loading ? "Saving…" : "Next: Term Weights →"}
          </button>
        </div>
      )}

      {phase === "weights" && (
        <div style={{ maxWidth: 560 }}>
          <h2 style={h2}>Step 3: Term Weights (Optional)</h2>

          <label style={{ ...lbl, flexDirection: "row", alignItems: "center", gap: 12 }}>
            <input
              type="checkbox"
              checked={weightsEnabled}
              onChange={e => setWeightsEnabled(e.target.checked)}
            />
            Enable per-term weighting
          </label>

          {weightsEnabled && (
            <>
              <p style={{ color: "var(--crown-muted)", marginBottom: 12 }}>
                Weights stored as basis points (bp). Must sum to exactly 10 000 bp = 100 %.
              </p>
              <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 12 }}>
                <thead>
                  <tr style={{ background: "var(--crown-surface-2)" }}>
                    <th style={th}>Term Code</th>
                    <th style={th}>Weight (bp)</th>
                    <th style={th}></th>
                  </tr>
                </thead>
                <tbody>
                  {weights.map((w, idx) => (
                    <tr key={idx}>
                      <td style={td}>
                        <input
                          type="text"
                          value={w.term_code}
                          onChange={e => updateWeight(idx, "term_code", e.target.value)}
                          placeholder="Q1"
                          style={{ ...inp, margin: 0 }}
                        />
                      </td>
                      <td style={td}>
                        <input
                          type="number"
                          min={1}
                          max={10000}
                          value={w.weight_bp}
                          onChange={e => updateWeight(idx, "weight_bp", e.target.value)}
                          placeholder="2500"
                          style={{ ...inp, margin: 0, width: 100 }}
                        />
                      </td>
                      <td style={td}>
                        {weights.length > 1 && (
                          <button onClick={() => removeWeight(idx)} style={rmBtn}>✕</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <p style={{ color: "var(--crown-muted)", fontSize: 13 }}>
                Total: {weights.reduce((a, w) => a + (parseInt(w.weight_bp, 10) || 0), 0)} bp
                {" "}(need 10 000)
              </p>

              <button onClick={addWeight} style={{ ...btn, background: "var(--crown-muted)", marginBottom: 12 }}>
                + Add Term
              </button>
            </>
          )}

          {error && <p style={err}>{error}</p>}

          <div style={{ marginTop: 12 }}>
            <button onClick={handleCommit} disabled={loading} style={btn}>
              {loading ? "Committing…" : "Commit Grade Scale ✓"}
            </button>
          </div>
        </div>
      )}

      {phase === "done" && result && (
        <div style={{ maxWidth: 520 }}>
          <h2 style={{ color: "var(--crown-ok)", marginBottom: 16 }}>✓ Grade Scale Committed</h2>
          <p>{result.message}</p>

          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 20 }}>
            <tbody>
              {[
                ["Academic Year",  result.academic_year_name],
                ["Scale Name",     result.scale_name],
                ["Scale Type",     result.scale_type],
                ["Rounding",       result.rounding],
                ["Bands Created",  result.bands_created],
                ["Bands Updated",  result.bands_updated],
                ["Weights Created",result.weights_created],
                ["Weights Updated",result.weights_updated],
                ["Scale ID",       result.scale_id],
              ].map(([label, val]) => (
                <tr key={label}>
                  <td style={{ padding: "6px 12px", fontWeight: 600, background: "var(--crown-surface-2)", width: "40%" }}>{label}</td>
                  <td style={{ padding: "6px 12px", fontFamily: "monospace" }}>{String(val ?? "—")}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <button onClick={reset} style={{ ...btn, marginTop: 24, background: "var(--crown-muted)" }}>
            Configure Another Scale
          </button>
        </div>
      )}
    </CrownLayout>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────────
const h2  = { marginBottom: 20 };
const lbl = { display: "flex", flexDirection: "column", fontWeight: 600, marginBottom: 16, fontSize: 14, gap: 4 };
const inp = { padding: "8px 10px", fontSize: 14, border: "1px solid var(--crown-border)", borderRadius: 4, marginTop: 4, width: "100%", boxSizing: "border-box" };
const btn = { padding: "10px 22px", background: "var(--crown-brand)", color: "var(--crown-surface)", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 15, fontWeight: 600, marginTop: 8 };
const err = { color: "var(--crown-danger)", marginTop: 8, fontSize: 14 };
const th  = { padding: "8px 10px", textAlign: "left", borderBottom: "2px solid var(--crown-border)", fontSize: 13 };
const td  = { padding: "6px 8px", borderBottom: "1px solid var(--crown-border)" };
const rmBtn = { background: "none", border: "none", cursor: "pointer", color: "var(--crown-danger)", fontSize: 18 };
