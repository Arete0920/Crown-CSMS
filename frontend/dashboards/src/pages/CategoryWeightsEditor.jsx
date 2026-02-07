import { useEffect, useMemo, useState } from "react";
import { getGradebookSections } from "../api/gradebook";
import { getSectionCategories, putCategoryWeightsBatch } from "../api/academicsWeights";

function sumActive(rows) {
  return rows
    .filter((r) => r.is_active)
    .reduce((acc, r) => acc + (Number(r.weight_percent) || 0), 0);
}

export function CategoryWeightsEditor() {
  const [sections, setSections] = useState([]);
  const [sectionId, setSectionId] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const activeSum = useMemo(() => sumActive(rows), [rows]);
  const sumOk = activeSum === 0 || Math.abs(activeSum - 100) < 0.01;

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setMsg("");
    getGradebookSections()
      .then((data) => {
        if (!alive) return;
        const sectionsList = Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [];
        setSections(sectionsList);
      })
      .catch((e) => {
        if (!alive) return;
        setMsg(`Failed to load sections: ${String(e)}`);
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  async function loadCategories(id) {
    setLoading(true);
    setMsg("");
    try {
      const data = await getSectionCategories(id);
      const normalized = (Array.isArray(data) ? data : []).map((c) => ({
        id: c.id,
        name: c.name ?? c.category_name ?? "(unnamed)",
        weight_percent: c.weight_percent ?? "0.00",
        is_active: Boolean(c.is_active),
        sort_order: c.sort_order ?? 9999,
      }));
      normalized.sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name));
      setRows(normalized);
    } catch (e) {
      setMsg(`Failed to load categories: ${String(e)}`);
      setRows([]);
    } finally {
      setLoading(false);
    }
  }

  async function save() {
    setMsg("");
    if (!sectionId) return setMsg("Select a section first.");
    if (!sumOk)
      return setMsg(
        `Active weights must total 100% (or set all inactive). Current: ${activeSum.toFixed(2)}%`
      );

    const payload = rows.map((r) => ({
      id: r.id,
      weight_percent: String(r.weight_percent),
      is_active: Boolean(r.is_active),
    }));

    setLoading(true);
    try {
      await putCategoryWeightsBatch(sectionId, payload);
      setMsg("✅ Saved successfully.");
      await loadCategories(sectionId);
    } catch (e) {
      setMsg(`❌ Save failed: ${String(e)}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 24, fontFamily: "system-ui, sans-serif", maxWidth: 1000 }}>
      <h2>Category Weights Editor</h2>

      <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 16 }}>
        <label style={{ fontWeight: 500 }}>
          Section:&nbsp;
          <select
            value={sectionId}
            onChange={async (e) => {
              const id = e.target.value;
              setSectionId(id);
              if (id) await loadCategories(id);
            }}
            style={{ padding: 6, minWidth: 300, fontSize: 14 }}
            disabled={loading}
          >
            <option value="">— Select a Section —</option>
            {sections.map((s) => (
              <option key={s.section_id} value={s.section_id}>
                {s.course_name || s.name || s.section_id}{" "}
                {s.roster_count > 0 ? `(${s.roster_count} students)` : "(empty)"}
              </option>
            ))}
          </select>
        </label>

        <button
          disabled={loading || !sectionId || !sumOk}
          onClick={save}
          style={{
            padding: "8px 16px",
            fontSize: 14,
            fontWeight: 500,
            cursor: loading || !sectionId || !sumOk ? "not-allowed" : "pointer",
            opacity: loading || !sectionId || !sumOk ? 0.5 : 1,
          }}
        >
          {loading ? "Saving..." : "Save All"}
        </button>

        <div style={{ marginLeft: "auto" }}>
          <span style={{ fontWeight: 500 }}>Active sum:</span>{" "}
          <b style={{ color: sumOk ? "green" : "red" }}>{activeSum.toFixed(2)}%</b>
          {!sumOk && <span style={{ color: "red", marginLeft: 8 }}>(must be 0 or 100)</span>}
        </div>
      </div>

      {msg && (
        <div
          style={{
            padding: 12,
            marginBottom: 16,
            background: msg.includes("✅") ? "#e6ffe6" : "#ffe6e6",
            border: `1px solid ${msg.includes("✅") ? "#00cc00" : "#cc0000"}`,
            borderRadius: 4,
          }}
        >
          {msg}
        </div>
      )}

      {rows.length === 0 && !loading && sectionId && (
        <div
          style={{
            padding: 24,
            background: "#f9f9f9",
            border: "1px solid #ddd",
            borderRadius: 4,
            textAlign: "center",
          }}
        >
          <p style={{ margin: 0, color: "#666" }}>
            No categories found for this section.
          </p>
        </div>
      )}

      {rows.length > 0 && (
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            border: "1px solid #ddd",
          }}
        >
          <thead>
            <tr style={{ background: "#f5f5f5" }}>
              <th
                style={{
                  textAlign: "left",
                  padding: "12px",
                  borderBottom: "2px solid #ddd",
                  fontWeight: 600,
                }}
              >
                Category Name
              </th>
              <th
                style={{
                  width: 120,
                  textAlign: "center",
                  padding: "12px",
                  borderBottom: "2px solid #ddd",
                  fontWeight: 600,
                }}
              >
                Active
              </th>
              <th
                style={{
                  width: 160,
                  textAlign: "center",
                  padding: "12px",
                  borderBottom: "2px solid #ddd",
                  fontWeight: 600,
                }}
              >
                Weight %
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr
                key={r.id}
                style={{
                  borderBottom: "1px solid #eee",
                  background: r.is_active ? "#fff" : "#fafafa",
                }}
              >
                <td style={{ padding: "10px 12px" }}>
                  <span style={{ fontWeight: r.is_active ? 500 : 400 }}>{r.name}</span>
                </td>
                <td style={{ textAlign: "center", padding: "10px 12px" }}>
                  <input
                    type="checkbox"
                    checked={r.is_active}
                    onChange={(e) => {
                      const next = [...rows];
                      next[idx] = { ...next[idx], is_active: e.target.checked };
                      setRows(next);
                    }}
                    style={{ width: 18, height: 18, cursor: "pointer" }}
                  />
                </td>
                <td style={{ padding: "10px 12px" }}>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={r.weight_percent}
                    onChange={(e) => {
                      const next = [...rows];
                      next[idx] = { ...next[idx], weight_percent: e.target.value };
                      setRows(next);
                    }}
                    style={{
                      width: "100%",
                      padding: "6px 8px",
                      fontSize: 14,
                      border: "1px solid #ddd",
                      borderRadius: 3,
                      textAlign: "right",
                    }}
                    disabled={!r.is_active}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={{ marginTop: 16, fontSize: 13, color: "#666" }}>
        <p style={{ margin: "4px 0" }}>
          <strong>Instructions:</strong>
        </p>
        <ul style={{ margin: "4px 0 0 0", paddingLeft: 20 }}>
          <li>Select a section to load its assignment categories</li>
          <li>Check "Active" for categories you want included in grade calculations</li>
          <li>Set weight percentages for active categories (must total 100%)</li>
          <li>To disable weighted grading, set all categories inactive (sum = 0)</li>
          <li>Click "Save All" to update weights atomically</li>
        </ul>
      </div>
    </div>
  );
}
