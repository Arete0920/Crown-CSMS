/**
 * RoomSetupWizard.jsx
 * Wizard #23 — Rooms Setup
 */
import { useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import { apiFetch } from "../lib/api.js";

const BASE = "/api/v1/room-setup-wizard/sessions/";

async function _post(path, body) {
  const r = await apiFetch(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(json.error || `HTTP ${r.status}`);
  return json;
}

function emptyRoom() { return { code: "", name: "", capacity: 30 }; }

export default function RoomSetupWizard() {
  const [phase, setPhase] = useState("configure");
  const [rooms, setRooms] = useState([emptyRoom()]);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  function updateRow(i, k, v) {
    setRooms(prev => prev.map((row, idx) => idx === i ? { ...row, [k]: v } : row));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErr(null);
    try {
      const sess = await _post(BASE);
      const sid = sess.session_id;
      await _post(`${BASE}${sid}/configure/`, { rooms });
      const r = await _post(`${BASE}${sid}/commit/`);
      setResult(r);
      setPhase("done");
    } catch (ex) { setErr(ex.message); }
  }

  return (
    <CrownLayout title="Rooms Setup">
      {phase === "configure" && (
        <form onSubmit={handleSubmit}>
          <h2>Step 1 — Room Inventory</h2>
          {rooms.map((row, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <input placeholder="Code (e.g. 101)" value={row.code} onChange={e => updateRow(i, "code", e.target.value)} required />
              <input placeholder="Name" value={row.name} onChange={e => updateRow(i, "name", e.target.value)} />
              <input type="number" min="0" placeholder="Capacity" value={row.capacity} onChange={e => updateRow(i, "capacity", parseInt(e.target.value, 10))} />
            </div>
          ))}
          <button type="button" onClick={() => setRooms(p => [...p, emptyRoom()])}>+ Add Room</button>
          {err && <p style={{ color: "var(--crown-danger)" }}>{err}</p>}
          <button type="submit">Commit Rooms</button>
        </form>
      )}
      {phase === "done" && <div><h2>Done</h2><p>Created: {result?.created} · Updated: {result?.updated} · Total: {result?.total}</p></div>}
    </CrownLayout>
  );
}
