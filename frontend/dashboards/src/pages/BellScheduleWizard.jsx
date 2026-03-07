/**
 * BellScheduleWizard.jsx
 *
 * Wizard #19 � Bell Schedule / Day Template Seed
 *
 * Phases:
 *   1. Configure  � schedule name, mode (SINGLE_DAY | DAY_TEMPLATES), academic year ID
 *   2. Blocks     � define period blocks per template
 *                   SINGLE_DAY: 1 template (DEFAULT), N blocks
 *                   DAY_TEMPLATES: 2+ templates (e.g. A/B or MON-FRI), each with N blocks
 *   3. Done       � commit result: schedule_id, template_count, snapshot
 */
import { useState, useCallback } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/bell-schedule-wizard/sessions/";
const SCHEDULE_MODES = ["SINGLE_DAY", "DAY_TEMPLATES"];

function emptyBlock() {
  return { code: "", label: "", start_time: "", end_time: "", is_instructional: false, is_lunch: false, is_break: false };
}

function emptyTemplate(code = "") {
  return { template_code: code, blocks: [emptyBlock()] };
}

async function _post(path, body) {
  const r = await apiFetch(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(json.error || JSON.stringify(json.errors) || "Request failed");
  return json;
}

// ---------------------------------------------------------------------------
// Phase 1 � Configure
// ---------------------------------------------------------------------------

function PhaseConfig({ onDone }) {
  const [scheduleName, setScheduleName] = useState("");
  const [scheduleMode, setScheduleMode] = useState("SINGLE_DAY");
  const [academicYearId, setAcademicYearId] = useState("");
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = useCallback(async () => {
    setErr(null);
    if (!scheduleName.trim()) return setErr("schedule_name is required");
    if (!academicYearId.trim()) return setErr("academic_year_id is required");
    setBusy(true);
    try {
      const created = await _post(BASE, undefined);
      const sid = created.session_id;
      await _post(`${BASE}${sid}/configure/`, {
        schedule_name: scheduleName.trim(),
        schedule_mode: scheduleMode,
        academic_year_id: academicYearId.trim(),
      });
      onDone({ sessionId: sid, scheduleMode });
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }, [scheduleName, scheduleMode, academicYearId, onDone]);

  return (
    <section>
      <h3 style={{ marginBottom: 16 }}>Step 1 � Configure Bell Schedule</h3>
      <table style={{ borderCollapse: "collapse", width: "100%", maxWidth: 520 }}>
        <tbody>
          <tr>
            <td style={{ padding: "8px 12px 8px 0", fontWeight: 600, whiteSpace: "nowrap" }}>Schedule name</td>
            <td style={{ padding: "8px 0" }}>
              <input
                value={scheduleName}
                onChange={e => setScheduleName(e.target.value)}
                placeholder="e.g. Standard, Wed Chapel, A-Day"
                style={{ width: "100%", padding: "6px 8px", boxSizing: "border-box" }}
              />
            </td>
          </tr>
          <tr>
            <td style={{ padding: "8px 12px 8px 0", fontWeight: 600 }}>Schedule mode</td>
            <td style={{ padding: "8px 0" }}>
              <select value={scheduleMode} onChange={e => setScheduleMode(e.target.value)} style={{ padding: "6px 8px" }}>
                {SCHEDULE_MODES.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
              <div style={{ fontSize: 12, color: "var(--crown-muted)", marginTop: 4 }}>
                {scheduleMode === "SINGLE_DAY" ? "All days follow one pattern (1 template: DEFAULT)." : "Different day types (A/B or Mon-Fri) each have their own periods."}
              </div>
            </td>
          </tr>
          <tr>
            <td style={{ padding: "8px 12px 8px 0", fontWeight: 600, whiteSpace: "nowrap" }}>Academic year ID</td>
            <td style={{ padding: "8px 0" }}>
              <input
                value={academicYearId}
                onChange={e => setAcademicYearId(e.target.value)}
                placeholder="UUID of the academic year"
                style={{ width: "100%", padding: "6px 8px", boxSizing: "border-box", fontFamily: "monospace" }}
              />
            </td>
          </tr>
        </tbody>
      </table>
      {err && <p style={{ color: "red", marginTop: 12 }}>{err}</p>}
      <button
        onClick={handleSubmit}
        disabled={busy}
        style={{ marginTop: 16, padding: "8px 20px", fontWeight: 600 }}
      >
        {busy ? "Saving�" : "Next: Define Period Blocks ?"}
      </button>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Block table sub-component
// ---------------------------------------------------------------------------

function BlockTable({ blocks, onChange }) {
  const update = (i, field, val) => {
    const next = blocks.map((b, idx) => idx === i ? { ...b, [field]: val } : b);
    onChange(next);
  };
  const addBlock = () => onChange([...blocks, emptyBlock()]);
  const removeBlock = i => onChange(blocks.filter((_, idx) => idx !== i));

  return (
    <div>
      <table style={{ borderCollapse: "collapse", width: "100%", fontSize: 13 }}>
        <thead>
          <tr style={{ background: "var(--crown-surface-2)" }}>
            <th style={thS}>Code</th>
            <th style={thS}>Label</th>
            <th style={thS}>Start</th>
            <th style={thS}>End</th>
            <th style={thS}>Instructional</th>
            <th style={thS}>Lunch</th>
            <th style={thS}>Break</th>
            <th style={thS}></th>
          </tr>
        </thead>
        <tbody>
          {blocks.map((b, i) => (
            <tr key={i}>
              <td style={tdS}><input value={b.code} onChange={e => update(i, "code", e.target.value)} style={inputS} placeholder="P1" /></td>
              <td style={tdS}><input value={b.label} onChange={e => update(i, "label", e.target.value)} style={inputS} placeholder="Period 1" /></td>
              <td style={tdS}><input type="time" value={b.start_time} onChange={e => update(i, "start_time", e.target.value)} style={inputS} /></td>
              <td style={tdS}><input type="time" value={b.end_time} onChange={e => update(i, "end_time", e.target.value)} style={inputS} /></td>
              <td style={{ ...tdS, textAlign: "center" }}><input type="checkbox" checked={b.is_instructional} onChange={e => update(i, "is_instructional", e.target.checked)} /></td>
              <td style={{ ...tdS, textAlign: "center" }}><input type="checkbox" checked={b.is_lunch} onChange={e => update(i, "is_lunch", e.target.checked)} /></td>
              <td style={{ ...tdS, textAlign: "center" }}><input type="checkbox" checked={b.is_break} onChange={e => update(i, "is_break", e.target.checked)} /></td>
              <td style={tdS}><button onClick={() => removeBlock(i)} title="Remove block" style={{ color: "red", background: "none", border: "none", cursor: "pointer", fontSize: 16 }}>?</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button onClick={addBlock} style={{ marginTop: 8, fontSize: 12 }}>+ Add block</button>
    </div>
  );
}

const thS = { padding: "6px 8px", textAlign: "left", fontWeight: 600, border: "1px solid var(--crown-border)" };
const tdS = { padding: "4px 6px", border: "1px solid var(--crown-border)", verticalAlign: "middle" };
const inputS = { width: "100%", padding: "4px 6px", boxSizing: "border-box", border: "1px solid var(--crown-border)" };

// ---------------------------------------------------------------------------
// Phase 2 � Blocks
// ---------------------------------------------------------------------------

function PhaseBlocks({ sessionId, scheduleMode, onDone }) {
  const initTemplates = scheduleMode === "SINGLE_DAY"
    ? [emptyTemplate("DEFAULT")]
    : [emptyTemplate("A"), emptyTemplate("B")];

  const [templates, setTemplates] = useState(initTemplates);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const updateTemplateCode = (i, code) => setTemplates(ts => ts.map((t, idx) => idx === i ? { ...t, template_code: code } : t));
  const updateBlocks = (i, blocks) => setTemplates(ts => ts.map((t, idx) => idx === i ? { ...t, blocks } : t));
  const addTemplate = () => setTemplates(ts => [...ts, emptyTemplate("")]);
  const removeTemplate = i => setTemplates(ts => ts.filter((_, idx) => idx !== i));

  const handleSubmit = useCallback(async () => {
    setErr(null);
    setBusy(true);
    try {
      await _post(`${BASE}${sessionId}/blocks/`, { templates });
      const result = await _post(`${BASE}${sessionId}/commit/`, {});
      onDone(result);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  }, [sessionId, templates, onDone]);

  return (
    <section>
      <h3 style={{ marginBottom: 8 }}>Step 2 � Define Period Blocks</h3>
      {scheduleMode === "SINGLE_DAY" && (
        <p style={{ fontSize: 13, color: "var(--crown-muted)", marginBottom: 12 }}>
          SINGLE_DAY: one template (DEFAULT) applied to all days. Gaps between blocks are allowed.
        </p>
      )}
      {scheduleMode === "DAY_TEMPLATES" && (
        <p style={{ fontSize: 13, color: "var(--crown-muted)", marginBottom: 12 }}>
          DAY_TEMPLATES: define 2+ templates (e.g. A/B or MON/TUE/WED/THU/FRI), each with their own block set.
        </p>
      )}

      {templates.map((tpl, i) => (
        <div key={i} style={{ border: "1px solid var(--crown-border)", borderRadius: 6, padding: 12, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            {scheduleMode === "SINGLE_DAY" ? (
              <strong>Template: DEFAULT</strong>
            ) : (
              <>
                <label style={{ fontWeight: 600 }}>Template code:</label>
                <input
                  value={tpl.template_code}
                  onChange={e => updateTemplateCode(i, e.target.value.toUpperCase())}
                  placeholder="A, B, MON, TUE�"
                  style={{ padding: "4px 8px", width: 100, textTransform: "uppercase" }}
                />
                {templates.length > 2 && (
                  <button onClick={() => removeTemplate(i)} style={{ color: "red", background: "none", border: "none", cursor: "pointer" }}>? Remove</button>
                )}
              </>
            )}
          </div>
          <BlockTable blocks={tpl.blocks} onChange={blocks => updateBlocks(i, blocks)} />
        </div>
      ))}

      {scheduleMode === "DAY_TEMPLATES" && (
        <button onClick={addTemplate} style={{ fontSize: 12, marginBottom: 16 }}>+ Add template</button>
      )}

      {err && <p style={{ color: "red", marginTop: 8 }}>{err}</p>}
      <div style={{ marginTop: 8 }}>
        <button
          onClick={handleSubmit}
          disabled={busy}
          style={{ padding: "8px 20px", fontWeight: 600 }}
        >
          {busy ? "Committing�" : "Commit Bell Schedule ?"}
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Phase 3 � Done
// ---------------------------------------------------------------------------

function PhaseDone({ result, onReset }) {
  return (
    <section>
      <h3 style={{ marginBottom: 12, color: "var(--crown-ok)" }}>? Bell Schedule Committed</h3>
      <table style={{ borderCollapse: "collapse", marginBottom: 16 }}>
        <tbody>
          {[
            ["Schedule ID",   result.schedule_id],
            ["Name",          result.schedule_name],
            ["Mode",          result.schedule_mode],
            ["Active",        result.is_active ? "Yes" : "No"],
            ["Templates",     result.templates?.length ?? 0],
          ].map(([k, v]) => (
            <tr key={k}>
              <td style={{ padding: "4px 16px 4px 0", fontWeight: 600 }}>{k}</td>
              <td style={{ padding: "4px 0", fontFamily: "monospace", fontSize: 13 }}>{String(v)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {result.templates?.map((tpl, i) => (
        <div key={i} style={{ marginBottom: 10 }}>
          <strong>Template: {tpl.template_code}</strong> � {tpl.block_count} block{tpl.block_count !== 1 ? "s" : ""}
          <ul style={{ margin: "4px 0 0 20px", fontSize: 13 }}>
            {tpl.blocks.map(b => (
              <li key={b.code}>{b.code}: {b.start_time} � {b.end_time}</li>
            ))}
          </ul>
        </div>
      ))}
      <button onClick={onReset} style={{ marginTop: 16, padding: "8px 20px" }}>
        Set Up Another Bell Schedule
      </button>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Root wizard
// ---------------------------------------------------------------------------

export default function BellScheduleWizard() {
  const [phase, setPhase] = useState("configure");
  const [ctx, setCtx] = useState({});

  const handleConfigDone = useCallback((data) => {
    setCtx(data);
    setPhase("blocks");
  }, []);

  const handleBlocksDone = useCallback((result) => {
    setCtx(c => ({ ...c, result }));
    setPhase("done");
  }, []);

  const handleReset = useCallback(() => {
    setCtx({});
    setPhase("configure");
  }, []);

  return (
    <CrownLayout title="Bell Schedule" subtitle="Define daily period blocks for a school year">
      <div className="crown-card" style={{ padding: "22px 24px" }}>
        <div style={{ display: "flex", gap: 24, marginBottom: 20, fontSize: 13 }}>
          {["configure", "blocks", "done"].map((p, i) => (
            <span key={p} style={{ fontWeight: phase === p ? 700 : 400, color: phase === p ? "var(--crown-brand)" : "var(--crown-muted)" }}>
              {i + 1}. {p.charAt(0).toUpperCase() + p.slice(1)}
            </span>
          ))}
        </div>
        {phase === "configure" && <PhaseConfig onDone={handleConfigDone} />}
        {phase === "blocks" && (
          <PhaseBlocks
            sessionId={ctx.sessionId}
            scheduleMode={ctx.scheduleMode}
            onDone={handleBlocksDone}
          />
        )}
        {phase === "done" && <PhaseDone result={ctx.result} onReset={handleReset} />}
      </div>
    </CrownLayout>
  );
}
