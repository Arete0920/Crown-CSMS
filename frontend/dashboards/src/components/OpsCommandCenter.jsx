import { useEffect, useMemo, useState } from "react";
import { fetchOpsSummary, fetchOpsAlerts } from "../api/ops";

export default function OpsCommandCenter() {
  const [data, setData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [err, setErr] = useState("");
  const [deps, setDeps] = useState({});
  const [depErrors, setDepErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setErr("");
    setDepErrors([]);
    setLoading(true);
    try {
      const [s, a] = await Promise.all([fetchOpsSummary(), fetchOpsAlerts()]);
      setData(s);
      setAlerts(a.alerts || []);
      setDeps(a.deps || {});
      setDepErrors(a.errors || []);
    } catch (e) {
      setErr(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const proof = useMemo(() => {
    if (!data) return "";
    const c = data.counts || {};
    const alertLines = alerts.length > 0
      ? [
          `ALERTS: ${alerts.length} total`,
          ...alerts.slice(0, 3).map((a) => `  - [${a.severity}] ${a.title}`),
          alerts.length > 3 ? `  ... (${alerts.length - 3} more)` : "",
        ].filter(Boolean)
      : ["ALERTS: none (demo looks healthy)"];

    return [
      `CROWN OPS PROOF`,
      `ts=${data.ts}`,
      `build_sha=${data.build_sha}`,
      `demo_mode=${data.demo_mode}`,
      `school=${data.school?.name || "n/a"} (${data.school?.id || "n/a"})`,
      `year=${data.academic_year?.label || "n/a"} (${data.academic_year?.id || "n/a"})`,
      `seed_last=${data.seed_last?.name || "n/a"} @ ${data.seed_last?.created_at || "n/a"}`,
      `students=${c.students}`,
      `households=${c.households}`,
      `admissions_applications=${c.admissions_applications}`,
      `invoices=${c.invoices}`,
      `grade_entries=${c.grade_entries}`,
      `comms_threads=${c.comms_threads}`,
      `comms_messages=${c.comms_messages}`,
      "",
      ...alertLines,
    ].join("\n");
  }, [data, alerts]);

  async function copyProof() {
    try {
      await navigator.clipboard.writeText(proof);
      alert("Copied proof to clipboard.");
    } catch {
      alert("Copy failed (browser permissions).");
    }
  }

  const tiles = [
    ["Build SHA", data?.build_sha],
    ["Demo Mode", String(data?.demo_mode)],
    ["School", data?.school?.name],
    ["Academic Year", data?.academic_year?.label],
    ["Admissions Apps", data?.counts?.admissions_applications],
    ["Invoices", data?.counts?.invoices],
    ["Grade Entries", data?.counts?.grade_entries],
    ["Comms Messages", data?.counts?.comms_messages],
  ];

  return (
    <div style={{ padding: 16 }}>
      <h2>Ops Command Center</h2>
      <div style={{ marginBottom: 12 }}>
        <button onClick={load} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>{" "}
        <button onClick={copyProof} disabled={!proof}>
          Copy Proof
        </button>
      </div>

      {err && (
        <div style={{ padding: 12, border: "1px solid var(--crown-danger)", marginBottom: 12 }}>
          <strong>Error:</strong> {err}
        </div>
      )}

      {depErrors.length > 0 && (
        <div style={{ padding: 12, border: "1px solid var(--crown-warn)", backgroundColor: "var(--crown-warn-bg)", marginBottom: 12 }}>
          <strong style={{ color: "var(--crown-warn)" }}>Ops Alerts Degraded:</strong>
          <div style={{ fontSize: 12, marginTop: 8 }}>
            {depErrors.map((e, i) => (
              <div key={i} style={{ marginBottom: 4 }}>• {e}</div>
            ))}
          </div>
          <div style={{ fontSize: 11, marginTop: 8, color: "var(--crown-muted)" }}>
            Some alert rules may be unavailable. Deps: admissions={String(deps.admissions)}, finance={String(deps.finance)}, gradebook={String(deps.gradebook)}
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(180px, 1fr))", gap: 12 }}>
        {tiles.map(([k, v]) => (
          <div key={k} style={{ border: "1px solid var(--crown-border)", padding: 12, borderRadius: 8 }}>
            <div style={{ fontSize: 12, opacity: 0.7 }}>{k}</div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>{v ?? "n/a"}</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 16, padding: 12, border: "1px solid var(--crown-border)", borderRadius: 8 }}>
        <h3 style={{ marginTop: 0, marginBottom: 12 }}>Predictive Alerts (Lite)</h3>
        <div style={{ fontSize: 12, color: "var(--crown-muted)", marginBottom: 12 }}>
          Deterministic rules based on current demo data
        </div>
        {alerts.length === 0 ? (
          <div style={{ fontSize: 14, color: "var(--crown-muted)" }}>No alerts. Demo data looks healthy.</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {alerts.map((a) => (
              <div key={a.id} style={{ padding: 10, border: "1px solid var(--crown-border)", borderRadius: 4 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{a.title}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, textTransform: "uppercase", color: a.severity === "critical" ? "var(--crown-danger)" : a.severity === "warning" ? "var(--crown-warn)" : "var(--crown-muted)" }}>
                    {a.severity}
                  </span>
                </div>
                <div style={{ fontSize: 13, marginBottom: 6 }}>{a.detail}</div>
                {a.metric && (
                  <div style={{ fontSize: 11, color: "var(--crown-muted)", fontFamily: "var(--crown-font-mono)" }}>
                    metric: {a.metric} • value: {JSON.stringify(a.value)} • threshold: {JSON.stringify(a.threshold)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <h3 style={{ marginTop: 16 }}>Proof Block</h3>
      <pre style={{ border: "1px solid var(--crown-border)", padding: 12, borderRadius: 8, overflow: "auto" }}>
        {proof || "Loading..."}
      </pre>
    </div>
  );
}

