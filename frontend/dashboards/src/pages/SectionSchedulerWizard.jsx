/**
 * SectionSchedulerWizard.jsx
 * Advanced scheduler: place existing canonical sections into bell-schedule slots.
 * Course, section, staffing, room, and bell master data are selected rather than recreated.
 */
import { useState } from "react";
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
  return { section_id: "", day_template_id: "", period_block_id: "", room_id: "" };
}

export default function SectionSchedulerWizard() {
  const [phase, setPhase] = useState("configure");
  const [sessionId, setSessionId] = useState(null);
  const [academicYearId, setAcademicYearId] = useState("");
  const [termCode, setTermCode] = useState("");
  const [options, setOptions] = useState({ sections: [], rooms: [], day_templates: [] });
  const [placements, setPlacements] = useState([emptyPlacement()]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  function updatePlacement(index, key, value) {
    setPlacements((previous) => previous.map((row, rowIndex) => {
      if (rowIndex !== index) return row;
      if (key === "day_template_id") {
        return { ...row, day_template_id: value, period_block_id: "" };
      }
      return { ...row, [key]: value };
    }));
  }

  function blocksFor(row) {
    return options.day_templates.find((template) => template.day_template_id === row.day_template_id)?.blocks || [];
  }

  async function handleConfigure(event) {
    event.preventDefault();
    setError(null);
    try {
      const session = await post(BASE, {});
      setSessionId(session.session_id);
      await post(`${BASE}${session.session_id}/configure/`, {
        academic_year_id: academicYearId,
        term_code: termCode,
      });
      const selectable = await request(`${BASE}${session.session_id}/options/`, { method: "GET" });
      setOptions(selectable);
      setPhase("placements");
    } catch (exception) {
      setError(exception.message);
    }
  }

  async function handlePublish(event) {
    event.preventDefault();
    setError(null);
    try {
      const rows = placements.filter((row) => row.section_id);
      if (!rows.length) throw new Error("At least one canonical section placement is required.");
      await post(`${BASE}${sessionId}/sections/`, { sections: rows });
      const committed = await post(`${BASE}${sessionId}/commit/`, { confirm: true });
      const verified = await request(`${BASE}${sessionId}/verify/`, { method: "GET" });
      setResult({ ...committed, verified });
      setPhase("done");
    } catch (exception) {
      setError(exception.message);
    }
  }

  return (
    <CrownLayout
      title="Section Scheduler"
      subtitle="Place canonical sections into rooms and bell-schedule periods"
    >
      {phase === "configure" && (
        <form onSubmit={handleConfigure} className="crown-card" style={{ padding: 20 }}>
          <h2>Scheduling Scope</h2>
          <p>Select the academic year and canonical term. Existing sections, rooms, and bell periods load after validation.</p>
          <input
            className="crown-input"
            placeholder="Academic Year ID"
            value={academicYearId}
            onChange={(event) => setAcademicYearId(event.target.value)}
            required
            style={{ display: "block", marginBottom: 8, width: "100%" }}
          />
          <input
            className="crown-input"
            placeholder="Term Code (S1, Q1, etc.)"
            value={termCode}
            onChange={(event) => setTermCode(event.target.value.toUpperCase())}
            required
            style={{ display: "block", marginBottom: 8, width: "100%" }}
          />
          {error && <div className="crown-alert">{error}</div>}
          <button className="crown-btn crown-btn-primary" type="submit">Load Canonical Sections</button>
        </form>
      )}

      {phase === "placements" && (
        <form onSubmit={handlePublish} className="crown-card" style={{ padding: 20 }}>
          <h2>Section Placements</h2>
          <p>Staffing is inherited from canonical TeacherAssignment records. Publishing does not delete unrelated sections or placements.</p>
          {placements.map((row, index) => (
            <div key={index} style={{ display: "grid", gridTemplateColumns: "2fr 1.3fr 1.3fr 1.3fr auto", gap: 8, marginBottom: 10 }}>
              <select
                className="crown-input"
                value={row.section_id}
                onChange={(event) => updatePlacement(index, "section_id", event.target.value)}
                required
              >
                <option value="">Select canonical section</option>
                {options.sections.map((section) => (
                  <option key={section.section_id} value={section.section_id}>
                    {section.course_code} — {section.course_name} ({section.section_id.slice(0, 8)})
                  </option>
                ))}
              </select>

              <select
                className="crown-input"
                value={row.day_template_id}
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
                value={row.period_block_id}
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
                value={row.room_id}
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
                disabled={placements.length === 1}
                onClick={() => setPlacements((previous) => previous.filter((_, rowIndex) => rowIndex !== index))}
              >
                Remove
              </button>
            </div>
          ))}

          <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
            <button className="crown-btn" type="button" onClick={() => setPlacements((previous) => [...previous, emptyPlacement()])}>
              + Add Placement
            </button>
            <button className="crown-btn crown-btn-primary" type="submit">Publish Placements</button>
          </div>
          {error && <div className="crown-alert" style={{ marginTop: 12 }}>{error}</div>}
        </form>
      )}

      {phase === "done" && (
        <div className="crown-card" style={{ padding: 20 }}>
          <h2>Scheduling Verified</h2>
          <p>Created: {result?.created} · Updated: {result?.updated} · Total: {result?.total}</p>
          <p>Verified placements: {result?.verified?.count}</p>
        </div>
      )}
    </CrownLayout>
  );
}
