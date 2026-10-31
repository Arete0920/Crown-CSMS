import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import DashboardSection from "../components/layout/DashboardSection.jsx";
import { crownApiClient } from "../api/client.js";

const BASE = "/api/v1/aftercare/daycare";
const newRequestKey = () => crypto.randomUUID();
function friendlyError(e) {
  const detail = e?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (e?.response?.status >= 400) return "The server rejected the request. Refresh and verify the custody roster.";
  return "Server outcome could not be confirmed. Refresh and verify custody status before retrying.";
}

export default function DiademDirectorRosterPage() {
  const [sites, setSites] = useState(null);
  const [siteId, setSiteId] = useState("");
  const [roster, setRoster] = useState(null);
  const [candidates, setCandidates] = useState(null);
  const [pickup, setPickup] = useState(null);
  const [identityMethod, setIdentityMethod] = useState("");
  const [attested, setAttested] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [writeStateUnknown, setWriteStateUnknown] = useState(false);
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let live = true;
    setSites(null); setRoster(null); setCandidates(null); setPickup(null);
    setError(""); setLoading(true);
    crownApiClient.get(`${BASE}/sites/`).then(({ data }) => {
      if (!live) return;
      if (!Array.isArray(data?.sites)) throw new Error("Invalid Diadem site directory.");
      setSites(data.sites);
      setSiteId((current) => data.sites.some((site) => site.site_id === current) ? current : data.sites[0]?.site_id || "");
    }).catch((err) => { if (live) setError(friendlyError(err)); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [refresh]);

  useEffect(() => {
    if (!sites || !siteId) return;
    let live = true;
    setRoster(null); setCandidates(null); setPickup(null);
    setError(""); setLoading(true);
    Promise.allSettled([
      crownApiClient.get(`${BASE}/sites/${encodeURIComponent(siteId)}/roster/`),
      crownApiClient.get(`${BASE}/sites/${encodeURIComponent(siteId)}/scheduled/`),
    ]).then(([present, scheduled]) => {
      if (!live) return;
      const problems = [];
      const rosterVerified = present.status === "fulfilled" &&
        present.value.data?.site_id === siteId && Array.isArray(present.value.data?.rows);
      if (rosterVerified) {
        setRoster(present.value.data);
        // A verified custody roster resolves an uncertain write even when
        // admission lookups are denied because the organization is suspended.
        // A denied schedule does not block the supervised release path.
        setWriteStateUnknown(false);
      } else problems.push("Open custody roster unavailable. Do not retry custody actions.");
      if (scheduled.status === "fulfilled" && scheduled.value.data?.site_id === siteId && Array.isArray(scheduled.value.data?.rows)) {
        setCandidates(scheduled.value.data);
      } else problems.push("Scheduled intake unavailable or unauthorized.");
      if (problems.length) setError(problems.join(" "));
    }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [siteId, sites]);

  async function checkin(row) {
    if (busy || writeStateUnknown || !siteId) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await crownApiClient.post(`${BASE}/attendance/checkin/`, {
        site_id: siteId, room_id: row.room_id, child_id: row.child_id,
        program_code: row.program_code, request_key: newRequestKey(),
      });
      setNotice("Check-in was recorded. Refreshing authoritative custody roster.");
      setRefresh((n) => n + 1);
    } catch (e) {
      setWriteStateUnknown(true);
      setError("Check-in outcome needs verification. Refresh the live custody roster before any retry. " + friendlyError(e));
    }
    finally { setBusy(false); }
  }

  async function selectPickup(row) {
    if (busy) return;
    setPickup(null); setIdentityMethod(""); setAttested(false);
    setBusy(true); setError("");
    try {
      const response = await crownApiClient.get(`${BASE}/attendance/${encodeURIComponent(row.attendance_id)}/pickup-authorities/`);
      if (response.data?.attendance_id !== row.attendance_id || !Array.isArray(response.data.recipients))
        throw new Error("Pickup clearance response failed attendance validation.");
      setPickup({ row, recipients: response.data.recipients, selected: "" });
    } catch (e) { setError(friendlyError(e)); }
    finally { setBusy(false); }
  }

  async function releaseChild() {
    if (!pickup?.selected || !identityMethod || !attested || busy || writeStateUnknown) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await crownApiClient.post(`${BASE}/attendance/release/`, {
        site_id: siteId, room_id: pickup.row.room_id,
        attendance_id: pickup.row.attendance_id,
        guardian_authority_id: pickup.selected, request_key: newRequestKey(),
        identity_verified: true, identity_method: identityMethod,
      });
      setPickup(null); setIdentityMethod(""); setAttested(false);
      setNotice("Verified release recorded. Reloading custody roster.");
      setRefresh((n) => n + 1);
    } catch (e) {
      setWriteStateUnknown(true);
      setError("Release outcome NOT CONFIRMED. Verify the roster and child's actual status before any retry. " + friendlyError(e));
    }
    finally { setBusy(false); }
  }

  return (
    <CrownLayout title="Diadem Daycare & Preschool" subtitle="Live, school-scoped childcare custody operations">
      <DashboardSection title="Center">
        <label htmlFor="diadem-site">Childcare center </label>
        <select id="diadem-site" value={siteId} disabled={!sites?.length || loading || busy}
          onChange={(e) => setSiteId(e.target.value)}>
          {!siteId && <option value="">No center selected</option>}
          {sites?.map((site) => <option key={site.site_id} value={site.site_id}>{site.name}{site.is_active ? "" : " (inactive)"}</option>)}
        </select>{" "}
        <button type="button" disabled={loading || busy} onClick={() => setRefresh((n) => n + 1)}>Refresh from server</button>
        {loading && <p role="status">Loading authoritative records…</p>}
        {error && <p role="alert">{error}</p>}
        {notice && <p role="status">{notice}</p>}
        {writeStateUnknown && <p role="alert">The previous custody write is unconfirmed. Further custody actions remain disabled until a successful roster refresh.</p>}
        {!loading && sites?.length === 0 && <p>No authorized childcare centers available.</p>}
      </DashboardSection>
      <DashboardSection title="Currently under staff supervision">
        {roster ? <>
          <p>{roster.children_present} open custody record(s), observed {roster.as_of}.</p>
          <div style={{ overflowX: "auto" }}><table><thead><tr>
            <th scope="col">Child</th><th scope="col">Room</th><th scope="col">Program</th>
            <th scope="col">Checked in</th><th scope="col">Custody action</th>
          </tr></thead><tbody>
            {roster.rows.map((row) => <tr key={row.attendance_id}>
              <td>{row.child_name}</td><td>{row.room_name}</td><td>{row.program_code}</td>
              <td>{row.checked_in_at}</td><td><button type="button" disabled={busy || writeStateUnknown}
                onClick={() => selectPickup(row)}>Verify authorized pickup</button></td>
            </tr>)}
            {!roster.rows.length && <tr><td colSpan={5}>No open custody records.</td></tr>}
          </tbody></table></div>
        </> : <p>{loading ? "Loading roster…" : "Custody roster unavailable. No estimated records shown."}</p>}
      </DashboardSection>
      <DashboardSection title="Scheduled admissions — not yet checked in">
        <p>These are candidates only. The server rechecks staffing, capacity, custody and entitlement during each admission.</p>
        {candidates ? <div style={{ overflowX: "auto" }}><table><thead><tr>
          <th scope="col">Child</th><th scope="col">Room</th><th scope="col">Program</th><th scope="col">Action</th>
        </tr></thead><tbody>
          {candidates.rows.map((row) => <tr key={row.enrollment_id}>
            <td>{row.child_name}</td><td>{row.room_name}</td><td>{row.program_code}</td>
            <td><button type="button" disabled={busy || writeStateUnknown} onClick={() => checkin(row)}>Record check-in</button></td>
          </tr>)}
          {!candidates.rows.length && <tr><td colSpan={4}>No authorized scheduled arrivals returned.</td></tr>}
        </tbody></table></div> : <p>Scheduled intake unavailable or loading.</p>}
      </DashboardSection>
      {pickup && <DashboardSection title="Verified physical custody handoff">
        <div role="group" aria-label="Verify child release">
          <h3>{pickup.row.child_name}</h3>
          <p>Verify the actual recipient in person. Selecting a name is not proof of identity or permission to release a child.</p>
          <label htmlFor="diadem-recipient">Authorized pickup recipient</label>
          <select id="diadem-recipient" value={pickup.selected}
            disabled={busy} onChange={(e) => { setPickup({ ...pickup, selected: e.target.value }); setAttested(false); }}>
            <option value="">Select a verified recipient</option>
            {pickup.recipients.map((r) => <option key={r.guardian_authority_id} value={r.guardian_authority_id}>{r.guardian_name}</option>)}
          </select>
          {!pickup.recipients.length && <p role="alert">No currently verified pickup authority. Do not release; contact the Director.</p>}
          <label htmlFor="diadem-identity-method">Identity verification method</label>
          <select id="diadem-identity-method" value={identityMethod} disabled={busy}
            onChange={(e) => { setIdentityMethod(e.target.value); setAttested(false); }}>
            <option value="">Choose an approved method</option>
            <option value="GOVERNMENT_PHOTO_ID">Government photo ID inspected</option>
            <option value="APPROVED_PHOTO_ROSTER">Approved photo roster verified</option>
            <option value="PERSONALLY_KNOWN">Personally known by releasing staff</option>
          </select>
          <label><input type="checkbox" checked={attested} disabled={busy}
            onChange={(e) => setAttested(e.target.checked)} />
            I personally verified this individual and am physically transferring custody to them.
          </label>
          <p>Release is final and auditable. Current authority will be rechecked by the server.</p>
          <button type="button" disabled={busy || writeStateUnknown || !pickup.selected || !identityMethod || !attested}
            onClick={releaseChild}>Record verified release</button>{" "}
          <button type="button" disabled={busy} onClick={() => setPickup(null)}>Cancel</button>
        </div>
      </DashboardSection>}
    </CrownLayout>
  );
}
