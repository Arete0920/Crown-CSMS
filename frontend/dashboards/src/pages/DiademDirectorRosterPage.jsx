import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { crownApiClient } from "../api/client.js";
import DiademReleaseReview from "./DiademReleaseReview.jsx";
import { getSelectedSchoolId, SCHOOL_CONTEXT_CHANGE_EVENT } from "../utils/authClient.js";

const BASE = "/api/v1/aftercare/daycare";

export default function DiademDirectorRosterPage() {
  const [sites, setSites] = useState(null);
  const [siteId, setSiteId] = useState("");
  const [roster, setRoster] = useState(null);
  const [review, setReview] = useState(null);
  const [releaseMessage, setReleaseMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [schoolContext, setSchoolContext] = useState(getSelectedSchoolId);
  const [directoryScope, setDirectoryScope] = useState(null);
  const [rosterScope, setRosterScope] = useState(null);
  const currentSites = directoryScope === schoolContext ? sites : null;

  useEffect(() => {
    const onSchoolChange = () => { setReview(null); setReleaseMessage(""); setSchoolContext(getSelectedSchoolId()); };
    window.addEventListener(SCHOOL_CONTEXT_CHANGE_EVENT, onSchoolChange);
    window.addEventListener("focus", onSchoolChange);
    window.addEventListener("storage", onSchoolChange);
    return () => {
      window.removeEventListener(SCHOOL_CONTEXT_CHANGE_EVENT, onSchoolChange);
      window.removeEventListener("focus", onSchoolChange);
      window.removeEventListener("storage", onSchoolChange);
    };
  }, []);

  useEffect(() => {
    let live = true;
    setSites(null);
    setRoster(null);
    setReview(null);
    setSiteId("");
    setDirectoryScope(null);
    setRosterScope(null);
    setError("");
    setLoading(true);
    if (!schoolContext) {
      setError("Select an authenticated school before opening childcare records.");
      setLoading(false);
      return () => { live = false; };
    }
    crownApiClient.get(`${BASE}/sites/`).then(({ data }) => {
      if (!live || getSelectedSchoolId() !== schoolContext) return;
      if (!Array.isArray(data?.sites)) throw new Error("Invalid Diadem site response.");
      setDirectoryScope(schoolContext);
      setSites(data.sites);
      setSiteId((current) => data.sites.some((site) => site.site_id === current) ? current : data.sites[0]?.site_id || "");
    }).catch((err) => { if (live && getSelectedSchoolId() === schoolContext) setError(err.message || "Site directory unavailable."); })
      .finally(() => { if (live && getSelectedSchoolId() === schoolContext) setLoading(false); });
    return () => { live = false; };
  }, [refresh, schoolContext]);

  useEffect(() => {
    if (!currentSites || !siteId || !schoolContext) return;
    let live = true;
    setRoster(null);
    setReview(null);
    setRosterScope(null);
    setError("");
    setLoading(true);
    crownApiClient.get(`${BASE}/sites/${encodeURIComponent(siteId)}/roster/`)
      .then(({ data }) => {
        if (!live || getSelectedSchoolId() !== schoolContext) return;
        if (data?.site_id !== siteId || !Array.isArray(data?.rows) || data.children_present !== data.rows.length)
          throw new Error("Diadem roster failed site-scoping validation.");
        setRosterScope(schoolContext);
        setRoster(data);
      }).catch((err) => { if (live && getSelectedSchoolId() === schoolContext) setError(err.message || "Care roster unavailable."); })
      .finally(() => { if (live && getSelectedSchoolId() === schoolContext) setLoading(false); });
    return () => { live = false; };
  }, [siteId, currentSites, schoolContext]);

  const currentRoster = schoolContext && rosterScope === schoolContext
    && siteId && roster?.site_id === siteId
    && currentSites?.some((site) => site.site_id === siteId) ? roster : null;

  return (
    <CrownLayout title="Diadem Daycare & Preschool" subtitle="Live childcare custody roster — operational certification pending">
      <DashboardSection title="Center and classroom">
        <p>Source: authenticated, school-scoped Diadem services. No demo enrollment or attendance numbers are substituted.</p>
        <label htmlFor="diadem-site">Care center</label>{" "}
        <select id="diadem-site" value={siteId} disabled={!currentSites?.length || loading}
          onChange={(event) => { setReview(null); setReleaseMessage(""); setSiteId(event.target.value); }}>
          {!siteId && <option value="">No center selected</option>}
          {currentSites?.map((site) => <option key={site.site_id} value={site.site_id}>{site.name}{site.is_active ? "" : " (inactive)"}</option>)}
        </select>{" "}
        <button type="button" disabled={loading} onClick={() => { setReleaseMessage(""); setRefresh((n) => n + 1); }}>Refresh</button>
        {loading && <p role="status">Loading live Diadem records…</p>}
        {error && <p role="alert">{error}</p>}
        {!loading && currentSites?.length === 0 && <p>No authorized childcare centers available.</p>}
      </DashboardSection>
      <DashboardSection title="Children currently in care">
        {currentRoster ? <>
          <p role="status">{currentRoster.children_present} open custody record(s). Observed at {currentRoster.as_of}.</p>
          <div role="region" aria-label="Children in care roster" tabIndex={0} style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead><tr><th scope="col">Child</th><th scope="col">Room</th><th scope="col">Program</th><th scope="col">Checked in</th><th scope="col">Custody status</th><th scope="col">Pickup action</th></tr></thead>
              <tbody>
                {currentRoster.rows.map((row) => <tr key={row.attendance_id}>
                  <td>{row.child_name}</td><td>{row.room_name}</td><td>{row.program_code}</td>
                  <td>{row.checked_in_at}</td><td>Awaiting verified release</td>
                  <td><button type="button" onClick={() => setReview(row)}>Review pickup</button></td>
                </tr>)}
                {currentRoster.rows.length === 0 && <tr><td colSpan={6}>No open custody records returned for this center.</td></tr>}
              </tbody>
            </table>
          </div>
          {review && currentRoster.rows.some((row) => row.attendance_id === review.attendance_id) &&
            <DiademReleaseReview key={`${schoolContext}:${siteId}:${review.attendance_id}`}
              siteId={siteId} attendance={review} onCancel={() => setReview(null)}
              onReleased={() => { setReview(null); setReleaseMessage("Server-confirmed handoff. Verify the refreshed custody roster before proceeding."); setRefresh((n) => n + 1); }} />}
        </> : <p>{loading ? "Loading roster…" : "No verified roster available."}</p>}
        {releaseMessage && currentSites && <p role="status">{releaseMessage}</p>}
        <p>Only authorized staff can confirm verified release. New admission remains separately gated.</p>
      </DashboardSection>
    </CrownLayout>
  );
}
