/**
 * FeeScheduleWizard.jsx
 *
 * Wizard #14 — Fee Schedule Setup
 * Guides finance/admin staff through creating a fee schedule with line items.
 *
 * Steps:
 *   1. Configure — schedule name, term, effective date
 *   2. Lines     — add fee/tuition line items (code, label, amount, kind, frequency)
 *   3. Done      — commit and verify
 *
 * MVP implementation: collect form fields, POST to backend wizard sessions.
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/fee-schedule-wizard/sessions/";

const KIND_OPTIONS = [
  { value: "tuition", label: "Tuition" },
  { value: "fee",     label: "Fee" },
];

const FREQ_OPTIONS = [
  { value: "annual",    label: "Annual" },
  { value: "semester",  label: "Semester" },
  { value: "monthly",   label: "Monthly" },
  { value: "one_time",  label: "One-Time" },
];

function emptyLine() {
  return {
    code:        "",
    label:       "",
    amount_cents: 0,
    kind:        "fee",
    frequency:   "annual",
    is_required:  false,
    sort_order:   0,
  };
}

function formatCents(cents) {
  const n = Number(cents);
  if (!Number.isFinite(n)) return "";
  return (n / 100).toLocaleString(undefined, { style: "currency", currency: "USD" });
}

function Step({ title, children }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h3 style={{ marginBottom: 12 }}>{title}</h3>
      {children}
    </div>
  );
}

export default function FeeScheduleWizard() {
  const [phase, setPhase]         = useState("configure"); // configure | lines | done | error
  const [sessionId, setSessionId] = useState(null);
  const [result, setResult]       = useState(null);
  const [err, setErr]             = useState(null);
  const [busy, setBusy]           = useState(false);

  const [config, setConfig] = useState({
    schedule_name:  "",
    term:           "",
    effective_date: "",
  });

  const [lines, setLines] = useState([emptyLine()]);

  function configField(name) {
    return {
      value:    config[name],
      onChange: (e) => setConfig((c) => ({ ...c, [name]: e.target.value })),
    };
  }

  function lineField(idx, name) {
    return {
      value:    lines[idx][name],
      onChange: (e) => {
        const val = name === "amount_cents"
          ? parseInt(e.target.value, 10) || 0
          : name === "is_required"
          ? e.target.checked
          : name === "sort_order"
          ? parseInt(e.target.value, 10) || 0
          : e.target.value;
        setLines((ls) => ls.map((l, i) => i === idx ? { ...l, [name]: val } : l));
      },
    };
  }

  function addLine() {
    setLines((ls) => [...ls, { ...emptyLine(), sort_order: ls.length }]);
  }

  function removeLine(idx) {
    setLines((ls) => ls.filter((_, i) => i !== idx));
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

      setPhase("lines");
    } catch (ex) {
      setErr(ex.message || "Configure step failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleLines(e) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      // 3. Set lines
      await apiFetch(`${BASE}${sessionId}/lines/`, {
        method: "POST",
        body: JSON.stringify({ lines }),
      });

      // 4. Commit
      const committed = await apiFetch(`${BASE}${sessionId}/commit/`, { method: "POST" });

      // 5. Verify
      const verified = await apiFetch(`${BASE}${sessionId}/verify/`);

      setResult({ ...committed, ...verified });
      setPhase("done");
    } catch (ex) {
      setErr(ex.message || "Lines/commit step failed.");
    } finally {
      setBusy(false);
    }
  }

  if (phase === "error") {
    return (
      <CrownLayout title="Fee Schedule Setup" subtitle="Wizard #14 — Fee Schedule Setup">
        <Step title="Error">
          <p style={{ color: "red" }}>{err}</p>
          <button onClick={() => { setPhase("configure"); setErr(null); }}>Restart</button>
        </Step>
      </CrownLayout>
    );
  }

  if (phase === "done") {
    return (
      <CrownLayout title="Fee Schedule Setup" subtitle="Wizard #14 — Fee Schedule Setup">
        <Step title="Fee Schedule Created">
          <p style={{ color: "green" }}>
            {result?.message || "Fee schedule created successfully."}
          </p>
          <ul>
            <li><strong>Schedule ID:</strong> {result?.schedule_id}</li>
            <li><strong>Name:</strong> {result?.schedule_name}</li>
            <li><strong>Term:</strong> {result?.term}</li>
            <li><strong>Lines created:</strong> {result?.lines_created}</li>
            <li><strong>Lines updated:</strong> {result?.lines_updated}</li>
            <li><strong>Total lines:</strong> {result?.line_count}</li>
            {result?.deactivated_count > 0 && (
              <li><strong>Other schedules deactivated:</strong> {result.deactivated_count}</li>
            )}
          </ul>
          <button onClick={() => { setPhase("configure"); setResult(null); setSessionId(null); setConfig({ schedule_name: "", term: "", effective_date: "" }); setLines([emptyLine()]); }}>
            Create Another
          </button>
        </Step>
      </CrownLayout>
    );
  }

  if (phase === "lines") {
    return (
      <CrownLayout title="Fee Schedule Setup" subtitle="Wizard #14 — Fee Schedule Setup">
        <Step title="Step 2 of 2 — Fee Lines">
          {err && <p style={{ color: "red" }}>{err}</p>}
          <form onSubmit={handleLines}>
            {lines.map((line, idx) => (
              <div key={idx} style={{ border: "1px solid var(--crown-border)", borderRadius: 4, padding: 12, marginBottom: 12 }}>
                <div style={{ marginBottom: 6 }}>
                  <label>Code&nbsp;
                    <input
                      {...lineField(idx, "code")}
                      required
                      pattern="[A-Za-z0-9_\-]{1,32}"
                      title="1-32 alphanumeric, dash, or underscore"
                      style={{ width: 140 }}
                    />
                  </label>
                  &nbsp;
                  <label>Label&nbsp;
                    <input {...lineField(idx, "label")} required style={{ width: 200 }} />
                  </label>
                </div>
                <div style={{ marginBottom: 6 }}>
                  <label>Amount (cents)&nbsp;
                    <input type="number" min="0" {...lineField(idx, "amount_cents")} required style={{ width: 100 }} />
                  </label>
                  &nbsp;
                  <span style={{ color: "var(--crown-muted)", fontSize: "0.9em" }}>{formatCents(line.amount_cents)}</span>
                  &nbsp;
                  <label>Kind&nbsp;
                    <select {...lineField(idx, "kind")}>
                      {KIND_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </label>
                  &nbsp;
                  <label>Frequency&nbsp;
                    <select {...lineField(idx, "frequency")}>
                      {FREQ_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                  </label>
                </div>
                <div>
                  <label>
                    <input type="checkbox" checked={line.is_required} onChange={lineField(idx, "is_required").onChange} />
                    &nbsp;Required
                  </label>
                  &nbsp;&nbsp;
                  <label>Sort&nbsp;
                    <input type="number" min="0" {...lineField(idx, "sort_order")} style={{ width: 60 }} />
                  </label>
                  &nbsp;&nbsp;
                  {lines.length > 1 && (
                    <button type="button" onClick={() => removeLine(idx)} style={{ color: "red" }}>
                      Remove
                    </button>
                  )}
                </div>
              </div>
            ))}
            <div style={{ marginBottom: 12 }}>
              <button type="button" onClick={addLine}>+ Add Line</button>
            </div>
            <button type="submit" disabled={busy}>{busy ? "Saving…" : "Commit Schedule"}</button>
          </form>
        </Step>
      </CrownLayout>
    );
  }

  // phase === "configure"
  return (
    <CrownLayout title="Fee Schedule Setup" subtitle="Wizard #14 — Fee Schedule Setup">
      <Step title="Step 1 of 2 — Schedule Details">
        {err && <p style={{ color: "red" }}>{err}</p>}
        <form onSubmit={handleConfigure}>
          <div style={{ marginBottom: 10 }}>
            <label>Schedule Name&nbsp;
              <input {...configField("schedule_name")} required style={{ width: 280 }} />
            </label>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label>Term&nbsp;
              <input {...configField("term")} required placeholder="e.g. 2026-2027" style={{ width: 180 }} />
            </label>
          </div>
          <div style={{ marginBottom: 16 }}>
            <label>Effective Date&nbsp;
              <input type="date" {...configField("effective_date")} required />
            </label>
          </div>
          <button type="submit" disabled={busy}>{busy ? "Saving…" : "Next: Fee Lines →"}</button>
        </form>
      </Step>
    </CrownLayout>
  );
}
