/**
 * AdvancementDashboard  Stage 1 KPI overview
 * Calls /api/v1/advancement/summary/
 * Falls back to empty-state if API is unavailable.
 */
import { useState, useEffect } from "react";

function apiBase() {
  const base = (import.meta?.env?.VITE_API_BASE_URL || "").trim();
  return base.endsWith("/") ? base.slice(0, -1) : base;
}

function getSession() {
  try {
    return {
      token:    sessionStorage.getItem("crown.jwt.access") || "",
      schoolId: sessionStorage.getItem("crown.school.id")  || "",
    };
  } catch {
    return { token: "", schoolId: "" };
  }
}

function fmtCurrency(val) {
  return `$${Number(val || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export default function AdvancementDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const { token, schoolId } = getSession();
    const url = `${apiBase()}/api/v1/advancement/summary/`;
    const headers = { Accept: "application/json" };
    if (token)    headers["Authorization"] = `Bearer ${token}`;
    if (schoolId) headers["X-School-Id"] = schoolId;

    globalThis.fetch(url, { headers })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, []);

  if (loading) return <p aria-busy="true">Loading advancement data</p>;
  if (error)   return <p role="alert" style={{ color: "red" }}>Error: {error}</p>;
  if (!data)   return null;

  return (
    <div aria-label="Advancement Dashboard">
      <h2>Advancement Overview</h2>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16, marginBottom: 24 }}>
        <KpiCard label="Total Advancement Revenue" value={fmtCurrency(data.total_advancement_revenue)} />
        <KpiCard label="Donations"                  value={fmtCurrency(data.donation_revenue)} />
        <KpiCard label="Ticket Revenue"             value={fmtCurrency(data.ticket_revenue)} />
        <KpiCard label="Sponsorship Revenue"        value={fmtCurrency(data.sponsorship_revenue)} />
        <KpiCard label="Store Revenue"              value={fmtCurrency(data.store_revenue)} />
        <KpiCard label="Total Donors"               value={data.total_donors} />
        <KpiCard label="Tickets Sold"               value={data.tickets_sold_total} />
        <KpiCard label="Active Store Items"         value={data.store_items_active} />
      </div>

      {/* Active Campaigns */}
      <section aria-label="Active Campaigns" style={{ marginBottom: 24 }}>
        <h3>Active Campaigns</h3>
        {data.active_campaigns?.length === 0 && <p>No active campaigns.</p>}
        {data.active_campaigns?.map((c) => (
          <CampaignRow key={c.id} campaign={c} />
        ))}
      </section>

      {/* Top 10 Donors */}
      <section aria-label="Top Donors" style={{ marginBottom: 24 }}>
        <h3>Top 10 Donors</h3>
        <table aria-label="Top Donors Table" style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th scope="col" style={TH}>Name</th>
              <th scope="col" style={TH}>Type</th>
              <th scope="col" style={TH}>Lifetime Giving</th>
            </tr>
          </thead>
          <tbody>
            {data.top_donors?.map((d) => (
              <tr key={d.id}>
                <td style={TD}>{d.name}</td>
                <td style={TD}>{d.donor_type}</td>
                <td style={TD}>{fmtCurrency(d.lifetime_giving)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Active Events */}
      <section aria-label="Active Events">
        <h3>Active Events</h3>
        <table aria-label="Events Table" style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th scope="col" style={TH}>Event</th>
              <th scope="col" style={TH}>Date</th>
              <th scope="col" style={TH}>Tickets Sold</th>
              <th scope="col" style={TH}>Capacity</th>
              <th scope="col" style={TH}>Attendance %</th>
            </tr>
          </thead>
          <tbody>
            {data.active_events?.map((e) => (
              <tr key={e.id}>
                <td style={TD}>{e.name}</td>
                <td style={TD}>{new Date(e.date).toLocaleDateString()}</td>
                <td style={TD}>{e.tickets_sold}</td>
                <td style={TD}>{e.capacity || "Unlimited"}</td>
                <td style={TD}>{e.attendance_percent}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function KpiCard({ label, value }) {
  return (
    <div
      role="region"
      aria-label={label}
      style={{
        background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8,
        padding: "16px 20px", boxShadow: "0 1px 3px rgba(0,0,0,.06)",
      }}
    >
      <p style={{ margin: 0, fontSize: 13, color: "#64748b" }}>{label}</p>
      <p style={{ margin: "4px 0 0", fontSize: 22, fontWeight: 700, color: "#1e293b" }}>{value}</p>
    </div>
  );
}

function CampaignRow({ campaign }) {
  const pct = campaign.progress_percent || 0;
  return (
    <div style={{ marginBottom: 12, padding: "12px 16px", border: "1px solid #e2e8f0", borderRadius: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between" }}>
        <strong>{campaign.name}</strong>
        <span>{pct}%</span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${campaign.name} progress`}
        style={{ marginTop: 6, height: 8, background: "#e2e8f0", borderRadius: 4 }}
      >
        <div style={{ width: `${Math.min(pct, 100)}%`, height: "100%", background: "#6366f1", borderRadius: 4 }} />
      </div>
      <p style={{ margin: "4px 0 0", fontSize: 12, color: "#64748b" }}>
        Raised: {fmtCurrency(campaign.raised)} / Goal: {fmtCurrency(campaign.goal)}
      </p>
    </div>
  );
}

const TH = { padding: "8px 12px", textAlign: "left", borderBottom: "2px solid #e2e8f0", fontSize: 13, color: "#475569" };
const TD = { padding: "8px 12px", borderBottom: "1px solid #f1f5f9", fontSize: 14 };
