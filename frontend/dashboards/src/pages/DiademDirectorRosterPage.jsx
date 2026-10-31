import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { crownApiClient } from "../api/client.js";

const BASE = "/api/v1/aftercare/daycare";

export default function DiademDirectorRosterPage() {
  const [sites, setSites] = useState(null);
  const [siteId, setSiteId] = useState("");
  const [roster, setRoster] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let live = true;
    setSites(null);
    setRoster(null);
    setError("");
    setLoading(true);
    crownApiClient.get(`${BASE}/sites/`).then(({ data }) => {
      if (!live) return;
      if (!Array.isArray(data?.sites)) throw new Error("Invalid Diadem site response.");
      setSites(data.sites);
      setSiteId((current) => data.sites.some((site) => site.site_id === current) ? current : data.sites[0]?.site_id || "");
    }).catch((err) => { if (live) setError(err.message || "Site directory unavailable."); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [refresh]);

  useEffect(() => {
    if (!sites || !siteId) return;
    let live = true;
    setRoster(null);
    setError("");
    setLoading(true);
    crownApiClient.get(`${BASE}/sites/${encodeURIComponent(siteId)}/roster/`)
      .then(({ data }) => {
        if (!live) return;
        if (data?.site_id !== siteId || !Array.isArray(data?.rows))
          throw new Error("Diadem roster failed site-scoping validation.");
        setRoster(data);
      }).catch((err) => { if (live) setError(err.message || "Care roster unavailable."); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [siteId, sites]);

  return (
    <CrownLayout title="Diadem Daycare & Preschool" subtitle="Live childcare custody roster — operational certification pending">
      <DashboardSection title="Center and classroom">
        <p>Source: authenticated, school-scoped Diadem services. No demo enrollment or attendance numbers are substituted.</p>
        <label htmlFor="diadem-site">Care center</label>{" "}
        <select id="diadem-site" value={siteId} disabled={!sites?.length || loading}
          onChange={(event) => setSiteId(event.target.value)}>
          {!siteId && <option value="">No center selected</option>}
          {sites?.map((site) => <option key={site.site_id} value={site.site_id}>{site.name}{site.is_active ? "" : " (inactive)"}</option>)}
        </select>{" "}
        <button type="button" disabled={loading} onClick={() => setRefresh((n) => n + 1)}>Refresh</button>
        {loading && <p role="status">Loading live Diadem records…</p>}
        {error && <p role="alert">{error}</p>}
        {!loading && sites?.length === 0 && <p>No authorized childcare centers available.</p>}
      </DashboardSection>
      <DashboardSection title="Children currently in care">
        {roster ? <>
          <p role="status">{roster.children_present} open custody record(s). Observed at {roster.as_of}.</p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr><th scope="col">Child</th><th scope="col">Room</th><th scope="col">Program</th><th scope="col">Checked in</th><th scope="col">Custody status</th></tr></thead>
              <tbody>
                {roster.rows.map((row) => <tr key={row.attendance_id}>
                  <td>{row.child_name}</td><td>{row.room_name}</td><td>{row.program_code}</td>
                  <td>{row.checked_in_at}</td><td>Awaiting verified release</td>
                </tr>)}
                {roster.rows.length === 0 && <tr><td colSpan={5}>No open custody records returned for this center.</td></tr>}
              </tbody>
            </table>
          </div>
        </> : <p>{loading ? "Loading roster…" : "No verified roster available."}</p>}
        <p>Check-in and release remain restricted to authorized staff and are not activated by this read-only screen.</p>
      </DashboardSection>
    </CrownLayout>
  );
}
