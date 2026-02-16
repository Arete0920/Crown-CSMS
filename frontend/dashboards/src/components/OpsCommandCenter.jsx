import React, { useEffect, useMemo, useState } from "react";
import { fetchOpsSummary } from "../api/ops";

export default function OpsCommandCenter() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function load() {
    setErr("");
    setLoading(true);
    try {
      const j = await fetchOpsSummary();
      setData(j);
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
    ].join("\n");
  }, [data]);

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
        <div style={{ padding: 12, border: "1px solid #c00", marginBottom: 12 }}>
          <strong>Error:</strong> {err}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(180px, 1fr))", gap: 12 }}>
        {tiles.map(([k, v]) => (
          <div key={k} style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8 }}>
            <div style={{ fontSize: 12, opacity: 0.7 }}>{k}</div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>{v ?? "n/a"}</div>
          </div>
        ))}
      </div>

      <h3 style={{ marginTop: 16 }}>Proof Block</h3>
      <pre style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8, overflow: "auto" }}>
        {proof || "Loading..."}
      </pre>
    </div>
  );
}
