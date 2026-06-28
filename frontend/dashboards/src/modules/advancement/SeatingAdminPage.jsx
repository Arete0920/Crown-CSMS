/* eslint-disable react-hooks/set-state-in-effect */
/**
 * SeatingAdminPage  Seating Map layout editor (Stage 3)
 *
 * 1. Loads all seating maps for the current school.
 * 2. Shows current layout JSON (pretty-printed) in a textarea.
 * 3. Submits PUT to set-layout endpoint, which regenerates Seat rows.
 *
 * GET  /api/v1/advancement/seating-maps/            map list
 * POST /api/v1/advancement/seating/set-layout/      { seating_map_id, layout_json }
 *
 * Layout JSON schema:
 * {
 *   "sections": [
 *     { "name": "A", "rows": [ { "name": "1", "seats": 10 }, ... ] },
 *     ...
 *   ]
 * }
 */
import { useState, useEffect, useCallback } from "react";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}
function getSession() {
  try {
    return {
      token: sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id") || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}
function authHeaders() {
  const { token, schoolId } = getSession();
  const h = { Accept: "application/json", "Content-Type": "application/json" };
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (schoolId) h["X-School-Id"] = schoolId;
  return h;
}

const PLACEHOLDER_LAYOUT = JSON.stringify(
  {
    sections: [
      { name: "A", rows: [{ name: "1", seats: 10 }, { name: "2", seats: 10 }] },
      { name: "B", rows: [{ name: "1", seats: 8 }] },
    ],
  },
  null,
  2
);

export default function SeatingAdminPage() {
  const [maps, setMaps] = useState([]);
  const [selectedMapId, setSelectedMapId] = useState("");
  const [layoutText, setLayoutText] = useState(PLACEHOLDER_LAYOUT);
  const [loadingMaps, setLoadingMaps] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [parseError, setParseError] = useState(null);
  const [result, setResult] = useState(null); // { ok, seats_created }

  const loadMaps = useCallback(async () => {
    setLoadingMaps(true);
    setError(null);
    try {
      const res = await globalThis.fetch(`${apiBase()}/api/v1/advancement/seating-maps/`, {
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list = Array.isArray(data) ? data : (data.results || []);
      setMaps(list);
      if (list.length > 0) {
        setSelectedMapId(list[0].id);
        const existing = list[0].layout_json;
        if (existing && Object.keys(existing).length > 0) {
          setLayoutText(JSON.stringify(existing, null, 2));
        }
      }
    } catch (err) {
      setError(err.message || "Failed to load seating maps.");
    } finally {
      setLoadingMaps(false);
    }
  }, []);

  useEffect(() => {
    loadMaps();
  }, [loadMaps]);

  function handleMapChange(e) {
    const id = e.target.value;
    setSelectedMapId(id);
    setResult(null);
    setError(null);
    const found = maps.find((m) => m.id === id);
    if (found && found.layout_json && Object.keys(found.layout_json).length > 0) {
      setLayoutText(JSON.stringify(found.layout_json, null, 2));
    } else {
      setLayoutText(PLACEHOLDER_LAYOUT);
    }
  }

  function handleLayoutChange(e) {
    setLayoutText(e.target.value);
    setParseError(null);
    setResult(null);
  }

  async function handleSave(e) {
    e.preventDefault();
    setError(null);
    setParseError(null);
    setResult(null);

    let parsedLayout;
    try {
      parsedLayout = JSON.parse(layoutText);
    } catch {
      setParseError("Invalid JSON  please fix the layout before saving.");
      return;
    }

    if (!selectedMapId) {
      setError("No seating map selected.");
      return;
    }

    setSaving(true);
    try {
      const res = await globalThis.fetch(`${apiBase()}/api/v1/advancement/seating/set-layout/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          seating_map_id: selectedMapId,
          layout_json: parsedLayout,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || `HTTP ${res.status}`);
        return;
      }
      setResult(data);
    } catch (err) {
      setError(err.message || "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  const seatCount = (() => {
    try {
      const obj = JSON.parse(layoutText);
      let n = 0;
      for (const sec of obj.sections || []) {
        for (const row of sec.rows || []) {
          n += Number(row.seats || 0);
        }
      }
      return n;
    } catch {
      return null;
    }
  })();

  return (
    <div style={{ padding: "1.5rem", maxWidth: 760 }}>
      <h2 style={{ marginBottom: "0.25rem" }}>Seating Map Admin</h2>
      <p style={{ color: "#6b7280", marginBottom: "1.25rem" }}>
        Edit the JSON layout for a seating map. Saving regenerates all Seat rows  only do
        this before tickets are sold for the affected events.
      </p>

      {loadingMaps ? (
        <p style={{ color: "#6b7280" }}>Loading maps</p>
      ) : (
        <form onSubmit={handleSave}>
          {/* Map selector */}
          <label htmlFor="seating-map-select" style={{ display: "block", fontWeight: 500, marginBottom: "0.25rem" }}>`n            Seating Map`n          </label>
          {maps.length === 0 ? (
            <p style={{ color: "#9ca3af", marginBottom: "1rem" }}>
              No seating maps found. Create one via the API or admin.
            </p>
          ) : (
            <select
              value={selectedMapId}
              onChange={handleMapChange}
              style={{ width: "100%", padding: "0.45rem", borderRadius: 5, border: "1px solid #d1d5db", marginBottom: "1rem" }}
            >
              {maps.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          )}

          {/* Layout JSON editor */}
          <label htmlFor="seating-layout-json" style={{ display: "block", fontWeight: 500, marginBottom: "0.25rem" }}>`n            Layout JSON
            {seatCount !== null && (
              <span style={{ marginLeft: "0.5rem", fontWeight: 400, color: "#6b7280", fontSize: "0.875rem" }}>
                ({seatCount} seats)
              </span>
            )}
          </label>
          <textarea
            value={layoutText}
            onChange={handleLayoutChange}
            rows={18}
            spellCheck={false}
            style={{
              width: "100%",
              fontFamily: "monospace",
              fontSize: "0.85rem",
              padding: "0.6rem",
              borderRadius: 6,
              border: parseError ? "1.5px solid #ef4444" : "1px solid #d1d5db",
              marginBottom: "0.4rem",
              boxSizing: "border-box",
            }}
          />
          {parseError && (
            <div style={{ color: "#b91c1c", fontSize: "0.875rem", marginBottom: "0.75rem" }}>
              {parseError}
            </div>
          )}

          {/* Schema hint */}
          <details style={{ marginBottom: "1rem", fontSize: "0.82rem", color: "#6b7280" }}>
            <summary style={{ cursor: "pointer" }}>Layout schema</summary>
            <pre style={{ background: "#f3f4f6", borderRadius: 4, padding: "0.6rem", marginTop: "0.4rem" }}>
{`{
  "sections": [
    {
      "name": "A",
      "rows": [
        { "name": "1", "seats": 10 },
        { "name": "2", "seats": 10 }
      ]
    }
  ]
}`}
            </pre>
          </details>

          {error && (
            <div style={{ background: "#fee2e2", color: "#b91c1c", padding: "0.75rem", borderRadius: 6, marginBottom: "0.75rem" }}>
              {error}
            </div>
          )}
          {result?.ok && (
            <div style={{ background: "#dcfce7", color: "#15803d", padding: "0.75rem", borderRadius: 6, marginBottom: "0.75rem" }}>
               Layout saved  {result.seats_created} seats created.
            </div>
          )}

          <button
            type="submit"
            disabled={saving || maps.length === 0}
            style={{
              padding: "0.55rem 1.5rem",
              borderRadius: 6,
              border: "none",
              background: "#2563eb",
              color: "#fff",
              fontWeight: 500,
              cursor: saving || maps.length === 0 ? "not-allowed" : "pointer",
              opacity: saving || maps.length === 0 ? 0.6 : 1,
            }}
          >
            {saving ? "Saving" : "Save Layout"}
          </button>
        </form>
      )}
    </div>
  );
}

