/* eslint-disable react-hooks/set-state-in-effect */
/**
 * MovesPipelinePage  Major Gift Moves Management (Stage 3)
 *
 * Displays all active prospects grouped by pipeline stage.
 * Allows a staff user to transition a prospect to the next stage.
 *
 * GET  /api/v1/advancement/prospects/?active=true    prospect list
 * GET  /api/v1/advancement/moves/?prospect_id=X      move history
 * POST /api/v1/advancement/moves/transition/          stage transition
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

const STAGES = [
  "identified",
  "qualified",
  "cultivating",
  "soliciting",
  "stewarding",
  "closed_won",
  "closed_lost",
];

const STAGE_LABEL = {
  identified: "Identified",
  qualified: "Qualified",
  cultivating: "Cultivating",
  soliciting: "Soliciting",
  stewarding: "Stewarding",
  closed_won: "Closed Won",
  closed_lost: "Closed Lost",
};

const STAGE_COLOR = {
  identified: "#e0e7ff",
  qualified: "#dbeafe",
  cultivating: "#d1fae5",
  soliciting: "#fef9c3",
  stewarding: "#fce7f3",
  closed_won: "#dcfce7",
  closed_lost: "#fee2e2",
};

const CAPACITY_LABEL = {
  unknown: "Unknown",
  tier1: "Tier 1 ($10k+)",
  tier2: "Tier 2 ($5k$9.9k)",
  tier3: "Tier 3 ($1k$4.9k)",
  tier4: "Tier 4 (<$1k)",
};

const ACTION_TYPES = [
  ["call", "Call"],
  ["email", "Email"],
  ["meeting", "Meeting"],
  ["tour", "Tour"],
  ["event", "Event Invite"],
  ["proposal", "Proposal"],
  ["thank_you", "Thank You"],
  ["other", "Other"],
];

export default function MovesPipelinePage() {
  const [prospects, setProspects] = useState([]);
  const [latestMove, setLatestMove] = useState({}); // prospect_id  move
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null); // prospect being transitioned
  const [transitioning, setTransitioning] = useState(false);
  const [form, setForm] = useState({
    new_stage: "",
    action_type: "meeting",
    summary: "",
    notes: "",
  });
  const [successMsg, setSuccessMsg] = useState(null);

  const loadProspects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await globalThis.fetch(`${apiBase()}/api/v1/advancement/prospects/?active=true`, {
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const list = Array.isArray(data) ? data : (data.results || []);
      setProspects(list);

      // Load latest move for each prospect
      const moveMap = {};
      await Promise.all(
        list.map(async (p) => {
          const mr = await globalThis.fetch(
            `${apiBase()}/api/v1/advancement/moves/?prospect_id=${p.id}`,
            { headers: authHeaders() }
          );
          if (mr.ok) {
            const md = await mr.json();
            const moves = Array.isArray(md) ? md : (md.results || []);
            if (moves.length > 0) moveMap[p.id] = moves[0]; // ordered by -created_at
          }
        })
      );
      setLatestMove(moveMap);
    } catch (err) {
      setError(err.message || "Failed to load prospects.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProspects();
  }, [loadProspects]);

  function openTransition(prospect) {
    setSelected(prospect);
    const currentStage = latestMove[prospect.id]?.stage || "identified";
    const nextIdx = Math.min(STAGES.indexOf(currentStage) + 1, STAGES.length - 2);
    setForm({
      new_stage: STAGES[nextIdx],
      action_type: "meeting",
      summary: "",
      notes: "",
    });
    setError(null);
    setSuccessMsg(null);
  }

  async function handleTransition(e) {
    e.preventDefault();
    if (!selected) return;
    setTransitioning(true);
    setError(null);
    try {
      const res = await globalThis.fetch(`${apiBase()}/api/v1/advancement/moves/transition/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ prospect_id: selected.id, ...form }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.detail || `HTTP ${res.status}`);
        return;
      }
      setSuccessMsg(`Prospect moved to "${STAGE_LABEL[data.stage] || data.stage}"`);
      setSelected(null);
      await loadProspects();
    } catch (err) {
      setError(err.message || "Transition failed.");
    } finally {
      setTransitioning(false);
    }
  }

  // Group prospects by their latest stage
  const byStage = {};
  STAGES.forEach((s) => (byStage[s] = []));
  prospects.forEach((p) => {
    const stage = latestMove[p.id]?.stage || "identified";
    if (byStage[stage]) byStage[stage].push(p);
  });

  return (
    <div style={{ padding: "1.5rem" }}>
      <h2 style={{ marginBottom: "0.25rem" }}>Moves Pipeline  Major Gifts</h2>
      <p style={{ color: "#6b7280", marginBottom: "1rem" }}>
        Active prospects grouped by cultivation stage.
      </p>

      {successMsg && (
        <div style={{ background: "#dcfce7", color: "#15803d", padding: "0.75rem 1rem", borderRadius: 6, marginBottom: "1rem" }}>
           {successMsg}
        </div>
      )}
      {error && (
        <div style={{ background: "#fee2e2", color: "#b91c1c", padding: "0.75rem 1rem", borderRadius: 6, marginBottom: "1rem" }}>
          {error}
        </div>
      )}

      {loading ? (
        <p style={{ color: "#6b7280" }}>Loading prospects</p>
      ) : (
        <div style={{ display: "flex", gap: "0.75rem", overflowX: "auto", paddingBottom: "1rem" }}>
          {STAGES.map((stage) => (
            <div
              key={stage}
              style={{
                minWidth: 200,
                background: STAGE_COLOR[stage],
                borderRadius: 8,
                padding: "0.75rem",
                flex: "0 0 200px",
              }}
            >
              <div style={{ fontWeight: 600, fontSize: "0.85rem", marginBottom: "0.5rem" }}>
                {STAGE_LABEL[stage]}
                <span style={{ marginLeft: "0.4rem", background: "#fff", borderRadius: 12, padding: "1px 8px", fontSize: "0.75rem", fontWeight: 400 }}>
                  {byStage[stage].length}
                </span>
              </div>
              {byStage[stage].length === 0 && (
                <p style={{ color: "#9ca3af", fontSize: "0.8rem" }}>No prospects</p>
              )}
              {byStage[stage].map((p) => (
                <div
                  key={p.id}
                  style={{
                    background: "#fff",
                    borderRadius: 6,
                    padding: "0.6rem 0.75rem",
                    marginBottom: "0.5rem",
                    boxShadow: "0 1px 3px rgba(0,0,0,.08)",
                  }}
                >
                  <div style={{ fontSize: "0.82rem", fontWeight: 500 }}>
                    {CAPACITY_LABEL[p.capacity_tier] || p.capacity_tier}
                  </div>
                  {p.interest_tags && (
                    <div style={{ fontSize: "0.74rem", color: "#6b7280", marginTop: "0.2rem" }}>
                      {p.interest_tags}
                    </div>
                  )}
                  {stage !== "closed_won" && stage !== "closed_lost" && (
                    <button
                      onClick={() => openTransition(p)}
                      style={{
                        marginTop: "0.5rem",
                        fontSize: "0.75rem",
                        background: "#2563eb",
                        color: "#fff",
                        border: "none",
                        borderRadius: 4,
                        padding: "3px 10px",
                        cursor: "pointer",
                      }}
                    >
                      Advance
                    </button>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Transition modal */}
      {selected && (
        <div
          style={{
            position: "fixed", inset: 0, background: "rgba(0,0,0,.35)",
            display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setSelected(null); }}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => { if (e.key === "Escape") setSelected(null); }}
        >
          <div style={{ background: "#fff", borderRadius: 10, padding: "1.5rem", width: 400, maxWidth: "95vw" }}>
            <h3 style={{ marginBottom: "1rem" }}>Advance Prospect</h3>
            <form onSubmit={handleTransition}>
              <label htmlFor="moves-new-stage" style={{ display: "block", fontWeight: 500, marginBottom: "0.25rem" }}>`n                New Stage`n              </label>
              <select
                value={form.new_stage}
                onChange={(e) => setForm((f) => ({ ...f, new_stage: e.target.value }))}
                style={{ width: "100%", padding: "0.45rem", borderRadius: 5, border: "1px solid #d1d5db", marginBottom: "0.75rem" }}
                required
              >
                {STAGES.map((s) => (
                  <option key={s} value={s}>{STAGE_LABEL[s]}</option>
                ))}
              </select>

              <label htmlFor="moves-action-type" style={{ display: "block", fontWeight: 500, marginBottom: "0.25rem" }}>`n                Action Type`n              </label>
              <select
                value={form.action_type}
                onChange={(e) => setForm((f) => ({ ...f, action_type: e.target.value }))}
                style={{ width: "100%", padding: "0.45rem", borderRadius: 5, border: "1px solid #d1d5db", marginBottom: "0.75rem" }}
              >
                {ACTION_TYPES.map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>

              <label htmlFor="moves-summary" style={{ display: "block", fontWeight: 500, marginBottom: "0.25rem" }}>`n                Summary`n              </label>
              <input
                type="text"
                value={form.summary}
                onChange={(e) => setForm((f) => ({ ...f, summary: e.target.value }))}
                placeholder="Brief note on this action"
                style={{ width: "100%", padding: "0.45rem", borderRadius: 5, border: "1px solid #d1d5db", marginBottom: "0.75rem", boxSizing: "border-box" }}
              />

              <label htmlFor="moves-notes" style={{ display: "block", fontWeight: 500, marginBottom: "0.25rem" }}>`n                Notes`n              </label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                rows={3}
                style={{ width: "100%", padding: "0.45rem", borderRadius: 5, border: "1px solid #d1d5db", marginBottom: "1rem", boxSizing: "border-box" }}
              />

              {error && (
                <div style={{ color: "#b91c1c", marginBottom: "0.75rem", fontSize: "0.875rem" }}>{error}</div>
              )}

              <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  style={{ padding: "0.45rem 1rem", borderRadius: 5, border: "1px solid #d1d5db", background: "#f9fafb", cursor: "pointer" }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={transitioning}
                  style={{ padding: "0.45rem 1rem", borderRadius: 5, border: "none", background: "#2563eb", color: "#fff", cursor: "pointer", opacity: transitioning ? 0.6 : 1 }}
                >
                  {transitioning ? "Saving" : "Save Move"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

