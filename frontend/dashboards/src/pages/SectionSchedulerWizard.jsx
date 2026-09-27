/**
 * SectionSchedulerWizard.jsx
 * Advanced scheduler: place existing canonical sections into bell-schedule slots.
 * Course, section, staffing, room, and bell master data are selected rather than recreated.
 */
import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/section-scheduler-wizard/sessions/";

async function request(path, options = {}) {
  const response = await apiFetch(path, options);
  const json = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(json.error || json.detail || `HTTP ${response.status}`);
  return json;
}

async function post(path, body) {
  return request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
}

function emptyPlacement() {
  return { section_id: "", day_template_id: "", period_block_id: "", room_id: "", dirty: true };
}

export default function SectionSchedulerWizard() {
  const [scope, setScope] = useState({ academic_years: [], terms: [] });
  const [busy, setBusy] = useState(false);
  const [scopeLoading, setScopeLoading] = useState(true);
  const [phase, setPhase] = useState("configure");
  const [sessionId, setSessionId] = useState(null);
  const [academicYearId, setAcademicYearId] = useState("");
  const [termCode, setTermCode] = useState("");
  const [options, setOptions] = useState({ sections: [], rooms: [], day_templates: [] });
  const [placements, setPlacements] = useState([emptyPlacement()]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    request("/api/v1/scheduling-wizard/sessions/scope-options/", { method: "GET" })
      .then((data) => {
        if (!active) return;
        setScope(data);
        setAcademicYearId(data.academic_years.find((year) => year.is_current)?.academic_year_id || "");
      })
      .catch((exception) => { if (active) setError(exception.message); })
      .finally(() => { if (active) setScopeLoading(false); });
    return () => { active = false; };
  }, []);

  function updatePlacement(index, key, value) {
    setPlacements((previous) => previous.map((row, rowIndex) => {
      if (rowIndex !== index) return row;
      if (key === "day_template_id") {
        return { ...row, dirty: true, day_template_id: value, period_block_id: "" };
      }
      return { ...row, dirty: true, [key]: value };
    }));
  }

  function blocksFor(row) {
    return options.day_templates.find((template) => template.day_template_id === row.day_template_id)?.blocks || [];
  }

  async function handleConfigure(event) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const session = await post(BASE, {});
      setSessionId(session.session_id);
      await post(`${BASE}${session.session_id}/configure/`, {
        academic_year_id: academicYearId,
        term_code: termCode,
      });
      const selectable = await request(`${BASE}${session.session_id}/options/`, { method: "GET" });
      setOptions(selectable);
      setPlacements(selectable.placements.length ? selectable.placements.map((row) => ({ ...row, dirty: false })) : [emptyPlacement()]);
      setPhase("placements");
    } catch (exception) {
      setError(exception.message);
    } finally {
      setBusy(false);
    }
  }

  async function handlePublish(event) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const rows = placements.filter((row) => row.section_id && row.dirty).map(({ dirty, ...row }) => row);
      if (!rows.length) throw new Error("Make at least one placement change before publishing.");
      await post(`${BASE}${sessionId}/sections/`, { sections: rows });
      const committed = await post(`${BASE}${sessionId}/commit/`, { confirm: true });
      setResult(committed);
      setPhase("done");
      const verified = await request(`${BASE}${sessionId}/verify/`, { method: "GET" });
      setResult({ ...committed, verified });
    } catch (exception) {
      setError(exception.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <CrownLayout
      title="Kairos"
      subtitle="Master Scheduling for Christian Schools"
    >
      <img src="/brand/kairos.png" alt="Kairos — Master Scheduling for Christian Schools" style={{ width: 230, maxWidth: "100%" }} />
      {phase === "configure" && (
        <form onSubmit={handleConfigure} className="crown-card" style={{ padding: 20 }}>
          <h2>Scheduling Scope</h2>
          <p>Select the academic year and term to load classes, rooms, periods, and existing meetings.</p>
          <label htmlFor="kairos-year">Academic year</label>
          <select id="kairos-year" className="crown-input" value={academicYearId}
            disabled={busy || scopeLoading} required
            onChange={(event) => { setAcademicYearId(event.target.value); setTermCode(""); }}>
            <option value="">{scopeLoading ? "Loading school years…" : "Select academic year"}</option>
            {scope.academic_years.map((year) => <option key={year.academic_year_id} value={year.academic_year_id}>{year.name}</option>)}
          </select>
          <label htmlFor="kairos-term">Term</label>
          <select id="kairos-term" className="crown-input" value={termCode} disabled={busy || !academicYearId}
            onChange={(event) => setTermCode(event.target.value)} required>
            <option value="">Select term</option>
            {scope.terms.filter((term) => term.academic_year_id === academicYearId).map((term) =>
              <option key={term.term_id} value={term.code}>{term.name}</option>)}
          </select>
          {!scopeLoading && !scope.academic_years.length && <p>No academic years are available. Complete academic year setup first.</p>}
          {error && <div role="alert" className="crown-alert">{error}</div>}
          <button className="crown-btn crown-btn-primary" type="submit" disabled={busy || scopeLoading}>Load Schedule</button>
        </form>
      )}

      {phase === "placements" && (
        <form onSubmit={handlePublish} className="crown-card" style={{ padding: 20 }}>
          <h2>Section Placements</h2>
          <p>Teacher assignments come from your class setup. Edit a meeting to move it, or mark it for removal. Changes take effect when you publish.</p>
          {placements.map((row, index) => (
            <div key={index} style={{ display: "grid", gridTemplateColumns: "2fr 1.3fr 1.3fr 1.3fr auto", gap: 8, marginBottom: 10 }}>
              <select
                aria-label={`Class ${index + 1}`}
                disabled={busy || !!row.placement_id}
                className="crown-input"
                value={row.section_id}
                onChange={(event) => updatePlacement(index, "section_id", event.target.value)}
                required
              >
                <option value="">Select class</option>
                {options.sections.map((section) => (
                  <option key={section.section_id} value={section.section_id}>
                    {section.course_code} — {section.course_name} ({section.section_id.slice(0, 8)})
                  </option>
                ))}
              </select>

              <select
                className="crown-input"
                aria-label={`Day ${index + 1}`}
                disabled={busy || row.action === "remove"}
                value={row.day_template_id || ""}
                onChange={(event) => updatePlacement(index, "day_template_id", event.target.value)}
                required
              >
                <option value="">Day template</option>
                {options.day_templates.map((template) => (
                  <option key={template.day_template_id} value={template.day_template_id}>
                    {template.template_code}
                  </option>
                ))}
              </select>

              <select
                className="crown-input"
                aria-label={`Period ${index + 1}`}
                disabled={busy || row.action === "remove"}
                value={row.period_block_id || ""}
                onChange={(event) => updatePlacement(index, "period_block_id", event.target.value)}
                required
              >
                <option value="">Period block</option>
                {blocksFor(row).map((block) => (
                  <option key={block.period_block_id} value={block.period_block_id}>
                    {block.code} — {block.name}
                  </option>
                ))}
              </select>

              <select
                className="crown-input"
                aria-label={`Room ${index + 1}`}
                disabled={busy || row.action === "remove"}
                value={row.room_id || ""}
                onChange={(event) => updatePlacement(index, "room_id", event.target.value)}
              >
                <option value="">No room</option>
                {options.rooms.map((room) => (
                  <option key={room.room_id} value={room.room_id}>
                    {room.code} — {room.name}
                  </option>
                ))}
              </select>

              <button
                className="crown-btn"
                type="button"
                disabled={busy}
                onClick={() => setPlacements((previous) => row.placement_id
                  ? previous.map((item, rowIndex) => rowIndex === index
                    ? { ...item, action: item.action === "remove" ? "upsert" : "remove", dirty: true } : item)
                  : previous.filter((_, rowIndex) => rowIndex !== index))}
              >
                {row.action === "remove" ? "Keep meeting" : "Remove"}
              </button>
            </div>
          ))}

          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <button className="crown-btn" type="button" disabled={busy} onClick={() => setPlacements((previous) => [...previous, emptyPlacement()])}>
              + Add Placement
            </button>
            <button className="crown-btn crown-btn-primary" type="submit" disabled={busy}>Publish Changes</button>
          </div>
          {error && <div className="crown-alert" style={{ marginTop: 12 }}>{error}</div>}
        </form>
      )}

      {phase === "done" && (
        <div className="crown-card" style={{ padding: 20 }}>
          <h2>{result?.undone ? "Publication undone" : "Schedule published"}</h2>
          <p>Created: {result?.created} · Updated: {result?.updated} · Total: {result?.total}</p>
          <p>Verified placements: {result?.verified?.count}</p>
          {!result?.undone && <button type="button" className="crown-btn" disabled={busy} onClick={async () => {
            setBusy(true); setError(null);
            try {
              await post(`${BASE}${sessionId}/undo/`, { confirm: true });
              setResult((previous) => ({ ...previous, undone: true }));
            } catch (exception) { setError(exception.message); }
            finally { setBusy(false); }
          }}>Undo this publication</button>}
          <button type="button" className="crown-btn" disabled={busy} onClick={() => { setPhase("configure"); setResult(null); }}>Review another schedule</button>
          {error && <div role="alert">{error}</div>}
        </div>
      )}
    </CrownLayout>
  );
}
