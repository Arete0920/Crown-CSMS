import { useEffect, useState } from "react";
import CrownLayout from "../components/crown/CrownLayout.jsx";
import CrownCard from "../components/crown/CrownCard.jsx";
import CrownMetricCard from "../components/crown/CrownMetricCard.jsx";
import { CrownGrid, Col } from "../components/crown/CrownGrid.jsx";
import { authenticatedFetch, getAccessToken } from "../utils/authClient.js";

async function loadGrantor(url) {
  const response = await authenticatedFetch(url, {
    method: "GET", omitSchoolContext: true, cache: "no-store",
  });
  const data = await response.json();
  if (!data || typeof data !== "object") throw new Error("Invalid grantor response.");
  return data;
}

const money = (cents) => Number.isSafeInteger(cents) && cents >= 0
  ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(cents / 100)
  : "Unavailable";
const count = (value) => Number.isSafeInteger(value) && value >= 0 ? value : "Unavailable";

export default function JirehSGODashboard() {
  const token = getAccessToken();
  const [organizations, setOrganizations] = useState(null);
  const [membershipToken, setMembershipToken] = useState(null);
  const [organizationId, setOrganizationId] = useState("");
  const [overview, setOverview] = useState(null);
  const [overviewToken, setOverviewToken] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    // A previous member's grantor records must not remain visible when a
    // session ends or the authenticated principal changes.
    setOrganizations(null);
    setMembershipToken(null);
    setOrganizationId("");
    setOverview(null);
    setOverviewToken(null);
    setError("");
    setLoading(false);
    if (!token) return;
    let live = true;
    setLoading(true);
    loadGrantor("/api/v1/jireh-sgo/organizations/").then((data) => {
      if (!live) return;
      if (!Array.isArray(data.organizations) || data.funds_status !== "NONCASH_ONLY")
        throw new Error("Unexpected grantor scope.");
      setOrganizations(data.organizations);
      setMembershipToken(token);
      setOrganizationId(data.organizations[0]?.id || "");
      setError("");
    }).catch(() => {
      if (live) { setOverview(null); setOrganizations([]); setError("SGO membership could not be verified."); }
    }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [token, refresh]);

  useEffect(() => {
    if (!token || !organizationId || membershipToken !== token) {
      setOverview(null);
      setOverviewToken(null);
      return;
    }
    let live = true;
    setOverview(null);
    setOverviewToken(null);
    setLoading(true);
    loadGrantor("/api/v1/jireh-sgo/organizations/" + encodeURIComponent(organizationId) + "/overview/")
      .then((data) => {
        if (!live) return;
        if (data.organization?.id !== organizationId ||
            data.funds_status !== "NONCASH_ONLY" || !Array.isArray(data.programs))
          throw new Error("Grantor context mismatch.");
        setOverview(data);
        setOverviewToken(token);
        setError("");
      }).catch(() => {
        if (live) { setOverview(null); setError("Grantor data unavailable. No figures displayed."); }
      }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [token, organizationId, membershipToken]);

  // Keep page contents hidden during session changes, even before effects run.
  const verifiedMembership = Boolean(token && membershipToken === token && organizations?.length);
  const currentOrganization = verifiedMembership && organizations.some((organization) => String(organization.id) === String(organizationId));
  const currentOverview = currentOrganization && overviewToken === token && !loading
    && overview?.organization?.id === organizationId ? overview : null;

  return (
    <CrownLayout
      navigationScope="standalone"
      title="Jireh SGO"
      subtitle="Standalone scholarship grantor workspace — noncash pilot"
      right={<button type="button" disabled={!token || loading} onClick={() => {
        setOrganizations(null);
        setMembershipToken(null);
        setOverview(null);
        setOverviewToken(null);
        setError("");
        setLoading(true);
        setRefresh((value) => value + 1);
      }}>
        Refresh grantor records
      </button>}
    >
      <p>Authenticated organization-scoped records. No school tenant is selected or inferred.</p>
      <p role="note">Commitments are not funded, cleared, allocated, or paid. No settlement or payments are enabled.</p>
      {!token && <p role="alert">Authorized SGO sign-in is required.</p>}
      {token && loading && <p role="status">Verifying grantor membership and records…</p>}
      {token && error && <p role="alert">{error}</p>}
      {token && membershipToken === token && organizations?.length === 0 && !error &&
        <p role="status">No active SGO membership is assigned.</p>}
      {verifiedMembership && <CrownCard title="Grantor membership">
        <label htmlFor="sgo-organization">Grantor organization</label>{" "}
        <select id="sgo-organization" value={organizationId} disabled={loading}
          onChange={(event) => { setOverview(null); setOverviewToken(null); setError(""); setOrganizationId(event.target.value); }}>
          {organizations.map((organization) => <option key={organization.id} value={organization.id}>
            {organization.name} ({organization.role})
          </option>)}
        </select>
      </CrownCard>}
      {currentOverview && <>
        <CrownGrid>
          <Col span={12}><CrownCard title="Organization and authorization">
            <p><strong>{currentOverview.organization.name}</strong></p>
            <p>Authorized role: {currentOverview.role}</p>
            <p>Operational status: {currentOverview.status === "PILOT_SOURCE_ONLY" ? "Source-only pilot (not certified)" : "Unverified"}</p>
            <p>Source: authenticated Jireh SGO program overview. Aggregates represent recorded noncash activity only.</p>
          </CrownCard></Col>
          <Col span={4}><CrownMetricCard label="Programs" value={count(currentOverview.totals?.programs)} /></Col>
          <Col span={4}><CrownMetricCard label="Applications" value={count(currentOverview.totals?.applications)} /></Col>
          <Col span={4}><CrownMetricCard label="Noncash commitments" value={money(currentOverview.totals?.noncash_committed_cents)} hint="Not payments or settled funds" /></Col>
          <Col span={12}><CrownCard title="Versioned programs">
            {currentOverview.programs.length === 0
              ? <p>No versioned programs yet.</p>
              : <div role="region" aria-label="SGO programs" tabIndex={0} style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead><tr><th scope="col">Program</th><th scope="col">Year</th>
                    <th scope="col">Source</th><th scope="col">Policy</th>
                    <th scope="col">Applications</th><th scope="col">Eligible</th>
                    <th scope="col">Unreviewed</th><th scope="col">Noncash committed</th></tr></thead>
                  <tbody>{currentOverview.programs.map((row) => <tr key={row.id}>
                    <th scope="row">{row.name}</th><td>{row.year ?? "Unavailable"}</td>
                    <td>{row.source || "Unavailable"}</td><td>{row.policy_version || "Unavailable"}</td>
                    <td>{count(row.applications)}</td><td>{count(row.eligible)}</td>
                    <td>{count(row.unreviewed)}</td><td>{money(row.noncash_committed_cents)}</td>
                  </tr>)}</tbody>
                </table>
              </div>}
          </CrownCard></Col>
        </CrownGrid>
      </>}
    </CrownLayout>
  );
}
